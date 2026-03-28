#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────
# API Quest — VPS Setup Script
# Target: Fresh Ubuntu 22.04+ / Debian 12+ VPS
# Domain: apiquest.cc
#
# Usage:
#   1. SSH into your VPS as root
#   2. curl/scp this script to the server
#   3. chmod +x setup-vps.sh && ./setup-vps.sh
#
# What this script does:
#   - Creates a deploy user with sudo access
#   - Installs Docker, Docker Compose, Nginx, Certbot
#   - Configures UFW firewall (SSH, HTTP, HTTPS only)
#   - Configures Nginx as a reverse proxy with SSL
#   - Clones the repo and creates a production .env
# ─────────────────────────────────────────────────────────────────
set -euo pipefail

DOMAIN="apiquest.cc"
DEPLOY_USER="deploy"
REPO="https://github.com/ghemrich/apiquest.git"
APP_DIR="/home/${DEPLOY_USER}/apiquest"

# ── Must run as root ───────────────────────────────────────────
if [[ $EUID -ne 0 ]]; then
  echo "Error: Run this script as root."
  exit 1
fi

echo "==> Updating system packages"
apt-get update && apt-get upgrade -y
apt-get install -y git openssl curl

# ── Create deploy user ─────────────────────────────────────────
echo "==> Creating deploy user: ${DEPLOY_USER}"
if ! id "${DEPLOY_USER}" &>/dev/null; then
  adduser --disabled-password --gecos "" "${DEPLOY_USER}"
  usermod -aG sudo "${DEPLOY_USER}"
  # Allow sudo without password for deploy scripts
  echo "${DEPLOY_USER} ALL=(ALL) NOPASSWD:ALL" > "/etc/sudoers.d/${DEPLOY_USER}"
  chmod 440 "/etc/sudoers.d/${DEPLOY_USER}"

  # Copy authorized_keys from root so you can SSH as deploy
  if [[ -f /root/.ssh/authorized_keys ]]; then
    mkdir -p "/home/${DEPLOY_USER}/.ssh"
    cp /root/.ssh/authorized_keys "/home/${DEPLOY_USER}/.ssh/"
    chown -R "${DEPLOY_USER}:${DEPLOY_USER}" "/home/${DEPLOY_USER}/.ssh"
    chmod 700 "/home/${DEPLOY_USER}/.ssh"
    chmod 600 "/home/${DEPLOY_USER}/.ssh/authorized_keys"
  fi
fi

# ── Install Docker ─────────────────────────────────────────────
echo "==> Installing Docker"
if ! command -v docker &>/dev/null; then
  apt-get install -y ca-certificates curl gnupg
  install -m 0755 -d /etc/apt/keyrings
  rm -f /etc/apt/keyrings/docker.gpg
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --batch --yes --dearmor -o /etc/apt/keyrings/docker.gpg
  chmod a+r /etc/apt/keyrings/docker.gpg

  # Detect distro (works for Ubuntu and Debian)
  . /etc/os-release
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
    https://download.docker.com/linux/${ID} ${VERSION_CODENAME} stable" > /etc/apt/sources.list.d/docker.list

  apt-get update
  apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
fi

usermod -aG docker "${DEPLOY_USER}"
systemctl enable docker

# ── Install Nginx ──────────────────────────────────────────────
echo "==> Installing Nginx"
apt-get install -y nginx
systemctl enable nginx

# ── Install Certbot ────────────────────────────────────────────
echo "==> Installing Certbot"
apt-get install -y certbot python3-certbot-nginx

# ── Firewall ───────────────────────────────────────────────────
echo "==> Configuring UFW firewall"
apt-get install -y ufw
ufw allow OpenSSH
ufw allow 'Nginx Full'
ufw --force enable

# ── Clone repo ─────────────────────────────────────────────────
echo "==> Cloning repository"
if [[ ! -d "${APP_DIR}" ]]; then
  sudo -u "${DEPLOY_USER}" git clone "${REPO}" "${APP_DIR}"
fi

# ── Create production .env ─────────────────────────────────────
echo "==> Creating production .env"
ENV_FILE="${APP_DIR}/.env"
if [[ ! -f "${ENV_FILE}" ]]; then
  SECRET_KEY=$(openssl rand -hex 32)
  PG_PASSWORD=$(openssl rand -hex 16)
  cat > "${ENV_FILE}" <<EOF
POSTGRES_USER=apiquest
POSTGRES_PASSWORD=${PG_PASSWORD}
POSTGRES_DB=apiquest
DATABASE_URL=postgresql://apiquest:${PG_PASSWORD}@postgres:5432/apiquest
SECRET_KEY=${SECRET_KEY}
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
KAFKA_BOOTSTRAP_SERVERS=kafka:9092
REDIS_URL=redis://redis:6379/0
APP_ENV=production
DEBUG=false
EOF
  chown "${DEPLOY_USER}:${DEPLOY_USER}" "${ENV_FILE}"
  chmod 600 "${ENV_FILE}"
  echo "    Generated .env with random secrets"
else
  echo "    .env already exists — skipping"
fi

# ── Nginx config ───────────────────────────────────────────────
echo "==> Configuring Nginx"
cp "${APP_DIR}/deploy/nginx/apiquest.conf" /etc/nginx/sites-available/apiquest
ln -sf /etc/nginx/sites-available/apiquest /etc/nginx/sites-enabled/apiquest
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx

# ── SSL certificate ────────────────────────────────────────────
echo "==> Obtaining SSL certificate"
echo "    Make sure DNS for ${DOMAIN} points to this server first!"
read -rp "    Continue with SSL setup? (y/n) " ssl_choice
if [[ "${ssl_choice}" == "y" ]]; then
  certbot --nginx -d "${DOMAIN}" --non-interactive --agree-tos --redirect \
    --register-unsolicited-email || echo "    Certbot failed — run manually: certbot --nginx -d ${DOMAIN}"
fi

# ── Start the app ──────────────────────────────────────────────
echo "==> Starting API Quest"
cd "${APP_DIR}"
sudo -u "${DEPLOY_USER}" docker compose -f docker-compose.prod.yml up -d --build

# ── Harden SSH (last step — verify deploy access first) ───────
echo "==> Verifying deploy user SSH access before hardening"
if sudo -u "${DEPLOY_USER}" test -f "/home/${DEPLOY_USER}/.ssh/authorized_keys"; then
  KEY_COUNT=$(wc -l < "/home/${DEPLOY_USER}/.ssh/authorized_keys")
  if [[ "$KEY_COUNT" -gt 0 ]]; then
    echo "    ${KEY_COUNT} SSH key(s) found for ${DEPLOY_USER} — hardening SSH"
    sed -i 's/^#\?PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config
    sed -i 's/^#\?PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config
    systemctl restart sshd
  else
    echo "    WARNING: No SSH keys for ${DEPLOY_USER} — skipping SSH hardening"
    echo "    Run: ssh-copy-id deploy@${DOMAIN} then manually harden SSH"
  fi
else
  echo "    WARNING: No authorized_keys for ${DEPLOY_USER} — skipping SSH hardening"
  echo "    Run: ssh-copy-id deploy@${DOMAIN} then manually harden SSH"
fi

echo ""
echo "════════════════════════════════════════════════════════"
echo "  API Quest deployed!"
echo "  URL: https://${DOMAIN}"
echo "  Logs: docker compose -f docker-compose.prod.yml logs -f"
echo "  .env: ${ENV_FILE}"
echo "════════════════════════════════════════════════════════"
