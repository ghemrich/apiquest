from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["Root"])

LANDING_HTML = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>API Quest</title>
<style>
  *{margin:0;padding:0;box-sizing:border-box}
  body{background:#0d1117;color:#c9d1d9;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif;line-height:1.6;display:flex;justify-content:center;padding:3rem 1.5rem}
  .container{max-width:640px;width:100%}
  h1{font-size:2.2rem;font-weight:700;color:#e6edf3;margin-bottom:.25rem;letter-spacing:-.02em}
  .subtitle{color:#7d8590;font-size:1.05rem;margin-bottom:2.5rem}
  h2{font-size:.85rem;text-transform:uppercase;letter-spacing:.08em;color:#7d8590;margin-bottom:1rem}
  .steps{list-style:none;counter-reset:step}
  .steps li{counter-increment:step;position:relative;padding-left:2rem;margin-bottom:1.25rem}
  .steps li::before{content:counter(step);position:absolute;left:0;top:.05em;width:1.4rem;height:1.4rem;border-radius:50%;background:#161b22;border:1px solid #30363d;text-align:center;font-size:.75rem;line-height:1.4rem;color:#58a6ff;font-weight:600}
  .step-title{color:#e6edf3;font-weight:600;display:block}
  code{background:#161b22;border:1px solid #30363d;border-radius:4px;padding:.15em .35em;font-size:.875em;color:#79c0ff;font-family:"SFMono-Regular",Consolas,"Liberation Mono",Menlo,monospace}
  .divider{border:none;border-top:1px solid #21262d;margin:2rem 0}
  .links{display:flex;gap:1rem;flex-wrap:wrap}
  .links a{color:#58a6ff;text-decoration:none;font-size:.9rem;padding:.45rem .9rem;border:1px solid #30363d;border-radius:6px;transition:border-color .15s}
  .links a:hover{border-color:#58a6ff}
  .footer{margin-top:2.5rem;color:#484f58;font-size:.8rem}
</style>
</head>
<body>
<div class="container">
  <h1>API Quest</h1>
  <p class="subtitle">Learn APIs by using one. No frontend &mdash; just you and your HTTP client.</p>

  <h2>Getting Started</h2>
  <ol class="steps">
    <li>
      <span class="step-title">Create an account</span>
      <code>POST /api/v1/auth/register</code>
    </li>
    <li>
      <span class="step-title">Log in for a token</span>
      <code>POST /api/v1/auth/login</code>
    </li>
    <li>
      <span class="step-title">Authorize requests</span>
      Header: <code>Authorization: Bearer &lt;token&gt;</code>
    </li>
    <li>
      <span class="step-title">Browse learning tracks</span>
      <code>GET /api/v1/tracks</code>
    </li>
    <li>
      <span class="step-title">Solve challenges &amp; earn points</span>
      <code>POST /api/v1/challenges/{id}/submit</code>
    </li>
  </ol>

  <hr class="divider">

  <div class="links">
    <a href="/docs">API Docs</a>
    <a href="/api/v1/">API Root</a>
    <a href="/api/v1/leaderboard">Leaderboard</a>
  </div>

  <p class="footer">Use curl, HTTPie, Postman, or any HTTP client to play.</p>
</div>
</body>
</html>
"""


@router.get("/", response_class=HTMLResponse)
def landing():
    return LANDING_HTML


@router.get("/api/v1/")
def welcome():
    return {
        "welcome": "Welcome to API Quest!",
        "description": "API Quest is a gamified API learning platform. Everything happens through API calls — there is no frontend.",
        "getting_started": {
            "step_1": "Register an account: POST /api/v1/auth/register with {\"username\": \"your_name\", \"password\": \"your_password\"}",
            "step_2": "Login to get your token: POST /api/v1/auth/login with {\"username\": \"your_name\", \"password\": \"your_password\"}",
            "step_3": "Use your token: Add header 'Authorization: Bearer <your_token>' to all requests",
            "step_4": "View available tracks: GET /api/v1/tracks",
            "step_5": "Start solving challenges and earn points!",
        },
        "documentation": "/docs",
        "tools": "Use HTTPie, Postman, curl, or any HTTP client to interact with this API.",
    }
