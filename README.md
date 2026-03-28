# API Quest

Learn APIs by using one. No frontend — just you and your HTTP client.

**[apiquest.cc](https://apiquest.cc)**

## Quick Start

```bash
# Register
curl -X POST https://apiquest.cc/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "your_name", "password": "your_password"}'

# Login
curl -X POST https://apiquest.cc/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "your_name", "password": "your_password"}'

# Browse tracks
curl https://apiquest.cc/api/v1/tracks \
  -H "Authorization: Bearer <your_token>"
```

## Tracks

| # | Track | Difficulty |
|---|-------|------------|
| 1 | REST Fundamentals | Beginner |
| 2 | Query Mastery | Beginner |
| 3 | Auth & Security | Intermediate |
| 4 | Data Relationships | Intermediate |
| 5 | Error Detective | Advanced |
| 6 | Real-Time APIs | Advanced |
| 7 | System Design | Expert |

41 challenges across 7 tracks.

## Stack

Python · FastAPI · PostgreSQL · Redis · Kafka

## Links

- [API Docs](https://apiquest.cc/docs)
- [Report an Issue](https://github.com/ghemrich/apiquest/issues)

## License

MIT
