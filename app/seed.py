"""Seed script — populates tracks, challenges, and badges.

Usage:
    python -m app.seed
"""

from sqlalchemy.orm import Session

# Import all models so tables are created
import app.models  # noqa: F401
from app.database import Base, SessionLocal, engine
from app.models.challenge import Challenge, Difficulty, Track
from app.models.gamification import Badge

TRACKS = [
    {
        "title": "REST Fundamentals",
        "description": "Learn the basics of RESTful APIs — methods, paths, status codes, and payloads.",
        "difficulty": Difficulty.beginner,
        "order_index": 1,
    },
    {
        "title": "Query Mastery",
        "description": "Master query parameters — filtering, pagination, sorting, and field selection.",
        "difficulty": Difficulty.beginner,
        "order_index": 2,
    },
    {
        "title": "Auth & Security",
        "description": "Explore authentication, authorization, API keys, rate limits, and CORS.",
        "difficulty": Difficulty.intermediate,
        "order_index": 3,
    },
    {
        "title": "Data Relationships",
        "description": "Navigate nested resources, eager loading, many-to-many, and cascade operations.",
        "difficulty": Difficulty.intermediate,
        "order_index": 4,
    },
    {
        "title": "Error Detective",
        "description": "Debug broken APIs — typos, wrong methods, encoding, versioning, race conditions.",
        "difficulty": Difficulty.advanced,
        "order_index": 5,
    },
    {
        "title": "Real-Time APIs",
        "description": "Work with WebSockets, Server-Sent Events, heartbeats, and channel subscriptions.",
        "difficulty": Difficulty.advanced,
        "order_index": 6,
    },
    {
        "title": "System Design",
        "description": "Caching, batch operations, async processing, idempotency, webhooks, and resilience.",
        "difficulty": Difficulty.expert,
        "order_index": 7,
    },
]


# Challenges per track. Each entry: (title, desc, method, path, headers, query, body, points, hints, sandbox, time_limit)
CHALLENGES = {
    "REST Fundamentals": [
        ("Hello, API", "Make your first API request.", "GET", "/api/v1/sandbox/hello/", None, None, None, 50,
         ["What's the simplest HTTP request?", "No body, no headers needed", "Try the /hello endpoint", "GET /api/v1/sandbox/hello/", "Just send a GET request"],
         "/api/v1/sandbox/hello", 120),
        ("The Library", "Retrieve the list of all books.", "GET", "/api/v1/sandbox/books/", None, None, None, 50,
         ["Books are at the /books endpoint", "No query params needed", "Just a simple GET", "GET /api/v1/sandbox/books/", "Returns a paginated list of books"],
         "/api/v1/sandbox/books", 120),
        ("Specific Retrieval", 'Fetch the book "Design Patterns" by its ID.', "GET", "/api/v1/sandbox/books/3", None, None, None, 50,
         ["List all books to find its ID", "REST APIs use path parameters like /resource/{id}", "The book ID is 3", "GET /api/v1/sandbox/books/3", "Full path: GET /api/v1/sandbox/books/3"],
         "/api/v1/sandbox/books", 120),
        ("Adding to the Shelf", 'Add the book "Clean Code" by Robert C. Martin (2008) to the collection using POST.',
         "POST", "/api/v1/sandbox/books/", {"Content-Type": "application/json"}, None,
         {"title": "Clean Code", "author": "Robert C. Martin", "year": 2008}, 50,
         ["POST is the HTTP method for creating resources", "You need a Content-Type: application/json header",
          "The body is JSON with title, author, and year", 'Try: {"title": "Clean Code", "author": "Robert C. Martin", "year": 2008}',
          "POST /api/v1/sandbox/books/ with the JSON body"],
         "/api/v1/sandbox/books", None),
        ("Fix the Typo", 'Book 4 has a misspelled author name. Use PUT to fix it.',
         "PUT", "/api/v1/sandbox/books/4", {"Content-Type": "application/json"}, None,
         {"title": "Refactoring", "author": "Martin Fowler", "year": 2018}, 50,
         ["First GET /api/v1/sandbox/books/4 to see the current data", "Look carefully at the author name",
          "PUT replaces the entire resource — send all fields", "Content-Type must be application/json",
          'PUT /api/v1/sandbox/books/4 with {"title": "Refactoring", "author": "Martin Fowler", "year": 2018}'],
         "/api/v1/sandbox/books", None),
        ("Clearing the Shelf", "Delete the placeholder book with ID 99 from the shelf.", "DELETE", "/api/v1/sandbox/books/99", None, None, None, 50,
         ["Which HTTP method removes resources?", "DELETE method", "You need a specific book ID", "DELETE /api/v1/sandbox/books/99", "No body or headers needed"],
         "/api/v1/sandbox/books", 120),
        ("Status Code Detective", 'Trigger three errors on the books API and observe the status codes: (1) request a book that doesn\'t exist, (2) POST an invalid body, (3) try PATCH on /books/1. Then POST your findings as {"codes": [code1, code2, code3]} to /api/v1/sandbox/books/status-check — the endpoint will tell you which answers are correct.', "POST", "/api/v1/sandbox/books/status-check", None, None,
         {"codes": [404, 400, 405]}, 75,
         ["Try GET /api/v1/sandbox/books/99999 — what status code do you get?", "Try POSTing garbage to /api/v1/sandbox/books/", "Try PATCH /api/v1/sandbox/books/1", "The three codes are 404, 400, and 405", "POST {\"codes\": [404, 400, 405]} to /api/v1/sandbox/books/status-check"],
         "/api/v1/sandbox/books", None),
        ("The Content-Type Mystery", 'POST the book "Test Book" by "Test Author" (2026) to /api/v1/sandbox/books/content-type-mystery — the endpoint will tell you what Content-Type it received and whether it accepted your data. Experiment until the server accepts your book.', "POST", "/api/v1/sandbox/books/content-type-mystery", {"Content-Type": "application/json"}, None,
         {"title": "Test Book", "author": "Test Author", "year": 2026}, 75,
         ["Try POSTing without any Content-Type header and read the error", "The endpoint shows you what Content-Type it received", "415 means Unsupported Media Type", "JSON content type is application/json", 'Add Content-Type: application/json to your headers'],
         "/api/v1/sandbox/books", None),
    ],
    "Query Mastery": [
        ("Filter by Status", "Retrieve only the tasks that have been completed.", "GET", "/api/v1/sandbox/tasks/", None, {"status": "completed"}, None, 50,
         ["Use a query parameter", "The parameter name is status", "completed is one valid status", "?status=completed", "GET /api/v1/sandbox/tasks/?status=completed"],
         "/api/v1/sandbox/tasks", 120),
        ("Page Turner", "Use pagination to fetch page 3 with 10 items per page.", "GET", "/api/v1/sandbox/tasks/", None, {"page": "3", "per_page": "10"}, None, 50,
         ["Pagination uses page and per_page", "page=3 gets the third page", "per_page controls items per page", "?page=3&per_page=10", "Combine both parameters"],
         "/api/v1/sandbox/tasks", None),
        ("Sort It Out", "Sort tasks by creation date descending.", "GET", "/api/v1/sandbox/tasks/", None, {"sort": "-created_at"}, None, 50,
         ["The sort parameter controls ordering", "Prefix with - for descending", "Sort by created_at field", "?sort=-created_at", "Minus means newest first"],
         "/api/v1/sandbox/tasks", 120),
        ("Search Party", 'Search for tasks containing the keyword "database".', "GET", "/api/v1/sandbox/tasks/", None, {"search": "database"}, None, 50,
         ["There's a search parameter", "It does partial string matching", "Search for 'database'", "?search=database", "Case-insensitive search"],
         "/api/v1/sandbox/tasks", None),
        ("Combining Powers", 'Combine filtering, searching, sorting, and pagination: find completed tasks matching "API", sorted by priority descending, page 2 with 5 per page.', "GET", "/api/v1/sandbox/tasks/", None,
         {"status": "completed", "search": "API", "sort": "-priority", "page": "2", "per_page": "5"}, None, 75,
         ["Combine status, search, sort, and pagination", "status=completed&search=API", "Add sort=-priority", "page=2&per_page=5", "Chain all 5 parameters with &"],
         "/api/v1/sandbox/tasks", None),
        ("Field Selection", "Request only the title and status fields from the tasks endpoint.", "GET", "/api/v1/sandbox/tasks/", None, {"fields": "title,status"}, None, 75,
         ["The fields parameter selects which data to return", "Comma-separated list of field names", "fields=title,status", "Only title and status columns", "Sparse fieldsets reduce payload size"],
         "/api/v1/sandbox/tasks", None),
    ],
    "Auth & Security": [
        ("The Locked Door", "Log in with username player1 and password quest123 to receive an access token.", "POST", "/api/v1/sandbox/mock-auth/login", {"Content-Type": "application/json"}, None,
         {"username": "player1", "password": "quest123"}, 100,
         ["POST to the login endpoint", "Send credentials as JSON", "Username is player1", "Password is quest123", "Content-Type: application/json"],
         "/api/v1/sandbox/mock-auth", None),
        ("Bearer of Tokens", "Use your token to access a protected route.", "GET", "/api/v1/sandbox/mock-auth/profile", {"Authorization": "Bearer <access_token>"}, None, None, 100,
         ["The profile endpoint needs authentication", "Use the Authorization header", "Bearer token format", "Authorization: Bearer <your_token>", "Get a token from /login first"],
         "/api/v1/sandbox/mock-auth", None),
        ("Token Expired", "Refresh an expired token.", "POST", "/api/v1/sandbox/mock-auth/refresh", {"Content-Type": "application/json"}, None,
         {"refresh_token": "<refresh_token>"}, 100,
         ["Tokens expire — you need to refresh", "POST to /refresh endpoint", "Send the refresh_token in body", "You got it from /login", "Content-Type: application/json"],
         "/api/v1/sandbox/mock-auth", None),
        ("Role Play", "Access admin-only endpoint.", "GET", "/api/v1/sandbox/mock-auth/admin/users", {"Authorization": "Bearer <admin_token>"}, None, None, 100,
         ["This endpoint requires admin role", "player1 won't work here", "Log in as admin1", "Password: adminquest123", "Authorization: Bearer <admin_token>"],
         "/api/v1/sandbox/mock-auth", None),
        ("API Key vs Token", "Use an API key for external data.", "GET", "/api/v1/sandbox/mock-auth/external/data", {"X-API-Key": "sk_test_abc123xyz"}, None, None, 100,
         ["This endpoint uses API keys, not Bearer tokens", "The header name is X-API-Key", "The key starts with sk_test_", "sk_test_abc123xyz", "Different auth mechanisms for different use cases"],
         "/api/v1/sandbox/mock-auth", None),
        ("Rate Limited", "Discover rate limit headers.", "GET", "/api/v1/sandbox/mock-auth/limited", {"Authorization": "Bearer <token>"}, None, None, 100,
         ["This endpoint has rate limiting", "Check the response headers", "X-RateLimit-Limit shows the max", "X-RateLimit-Remaining shows what's left", "Retry-After tells you when to try again"],
         "/api/v1/sandbox/mock-auth", None),
        ("The CORS Preflight", "Send an OPTIONS request.", "OPTIONS", "/api/v1/sandbox/mock-auth/cors-test", None, None, None, 100,
         ["CORS uses preflight requests", "The HTTP method is OPTIONS", "Browsers send this automatically", "Check Access-Control-Allow-Origin in response", "OPTIONS /api/v1/sandbox/mock-auth/cors-test"],
         "/api/v1/sandbox/mock-auth", None),
        ("Input Sanitization", "Test the API's input validation by posting a user name containing an HTML <script> tag.", "POST", "/api/v1/sandbox/mock-auth/users", None, None,
         {"name": "<script>alert('hacked')</script>"}, 100,
         ["APIs should validate input", "Try sending HTML/script tags", "XSS protection rejects dangerous input", "Send a name with <script> tags", "The API should return 400"],
         "/api/v1/sandbox/mock-auth", None),
    ],
    "Data Relationships": [
        ("Nested Resources", "Retrieve all projects belonging to user 7.", "GET", "/api/v1/sandbox/users-data/7/projects", None, None, None, 100,
         ["Resources can be nested under others", "User 7 has projects", "/users-data/{user_id}/projects", "GET request, no body needed", "GET /api/v1/sandbox/users-data/7/projects"],
         "/api/v1/sandbox/users-data", None),
        ("Deep Nesting", "Retrieve all tasks for project 3 of user 7.", "GET", "/api/v1/sandbox/users-data/7/projects/3/tasks", None, None, None, 100,
         ["Go deeper: user → project → tasks", "Three levels of nesting", "User 7, Project 3", "/7/projects/3/tasks", "GET /api/v1/sandbox/users-data/7/projects/3/tasks"],
         "/api/v1/sandbox/users-data", None),
        ("Include Related Data", "Use eager loading to include tasks.", "GET", "/api/v1/sandbox/users-data/projects/3", None, {"include": "tasks"}, None, 100,
         ["The include parameter embeds related data", "include=tasks adds tasks to the response", "Alternative to nested resource URLs", "?include=tasks", "GET /projects/3?include=tasks"],
         "/api/v1/sandbox/users-data", None),
        ("Creating with Relationships", 'Create a new high-priority task titled "Write unit tests" linked to project 3.', "POST", "/api/v1/sandbox/users-data/tasks", None, None,
         {"title": "Write unit tests", "project_id": 3, "priority": "high"}, 100,
         ["POST to create a new task", "Link it to project 3 via project_id", "Include title and priority", "project_id: 3", "POST /api/v1/sandbox/users-data/tasks"],
         "/api/v1/sandbox/users-data", None),
        ("Many-to-Many", "Add user 5 to team 2.", "POST", "/api/v1/sandbox/users-data/teams/2/members", None, None,
         {"user_id": 5}, 100,
         ["Teams and users are many-to-many", "POST to add a member", "/teams/2/members", "Send user_id in body", "POST with {\"user_id\": 5}"],
         "/api/v1/sandbox/users-data", None),
        ("Cascade Effects", "Delete project 3 and observe what happens to its tasks. Warning: this is destructive — do the other Data Relationships challenges first!", "DELETE", "/api/v1/sandbox/users-data/projects/3", None, None, None, 100,
         ["DELETE removes the resource", "What happens to child resources?", "Tasks belong to the project", "Cascade delete removes children too", "DELETE /api/v1/sandbox/users-data/projects/3"],
         "/api/v1/sandbox/users-data", None),
    ],
    "Error Detective": [
        ("The Silent Failure", "Fix the typo in the query param.", "GET", "/api/v1/sandbox/broken/items", None, {"status": "active"}, None, 150,
         ["The API has a subtle bug", "Check what happens with staus vs status", "One is a typo that silently fails", "Use the correct spelling: status", "?status=active with correct spelling"],
         "/api/v1/sandbox/broken", None),
        ("The Wrong Method", 'Update item 10 with name "Updated Item" and status "active" — not every write uses POST.', "PUT", "/api/v1/sandbox/broken/items/10", {"Content-Type": "application/json"}, None,
         {"name": "Updated Item", "status": "active"}, 150,
         ["POST returns 405 Method Not Allowed", "Which method is for updates?", "PUT replaces the resource", "Content-Type: application/json", "PUT /api/v1/sandbox/broken/items/10"],
         "/api/v1/sandbox/broken", None),
        ("Missing Required Fields", 'Create an order for a "Widget" (quantity: 5) shipped to "123 Main St". The API will tell you if anything is missing.', "POST", "/api/v1/sandbox/broken/orders", None, None,
         {"product": "Widget", "quantity": 5, "shipping_address": "123 Main St"}, 150,
         ["Read the 422 error carefully", "It tells you which field is missing", "shipping_address is required", "Include product, quantity, and shipping_address", "All three fields are mandatory"],
         "/api/v1/sandbox/broken", None),
        ("The Encoding Trap", 'Search for "hello world" — but watch out for how spaces travel in URLs.', "GET", "/api/v1/sandbox/broken/search", None, {"q": "hello world"}, None, 150,
         ["Spaces in URLs need encoding", "%20 or + replaces spaces", "q=hello%20world", "URL encoding is essential", "The query is 'hello world'"],
         "/api/v1/sandbox/broken", None),
        ("Version Mismatch", "Use the correct API version.", "GET", "/api/v1/sandbox/broken/v2/products/1", None, None, None, 150,
         ["APIs evolve over versions", "v1 has fewer fields than v2", "v2 includes description and category", "Use /v2/ not /v1/", "GET /api/v1/sandbox/broken/v2/products/1"],
         "/api/v1/sandbox/broken", None),
        ("The Timeout", "Add a limit to avoid timeout.", "GET", "/api/v1/sandbox/broken/heavy-data", None, {"limit": "50"}, None, 150,
         ["Without a limit, the request times out", "504 means Gateway Timeout", "Add a limit parameter", "Keep it under 100", "?limit=50"],
         "/api/v1/sandbox/broken", None),
        ("Race Condition", "Safely update document 1 using its ETag — first GET the document to discover the current ETag, then PUT with If-Match.", "PUT", "/api/v1/sandbox/broken/documents/1",
         {"If-Match": '"<etag>"', "Content-Type": "application/json"}, None,
         {"title": "Updated Document"}, 150,
         ["GET /api/v1/sandbox/broken/documents/1 to get the ETag", "The ETag is in the response headers", "Use If-Match header with the ETag value", "412 means your ETag is stale", "PUT with If-Match and Content-Type: application/json"],
         "/api/v1/sandbox/broken", None),
        ("The Broken Chain", "Start a 3-step API chain by requesting the first token.", "GET", "/api/v1/sandbox/broken/step1", None, None, None, 150,
         ["This chain has three steps", "Step 1 gives you a token", "Step 2 uses that token: /step2?token=X", "Step 3 uses the ID from step 2: /step3/{id}", "Begin with GET /api/v1/sandbox/broken/step1"],
         "/api/v1/sandbox/broken", None),
    ],
    "Real-Time APIs": [
        ("Your First WebSocket", 'Connect to the chat WebSocket and send "Hello from API Quest!".', "GET", "/api/v1/sandbox/stream/chat", None, None,
         {"text": "Hello from API Quest!"}, 150,
         ["WebSockets use ws:// protocol", "Connect to /stream/chat", "Send a JSON message", "{\"text\": \"Hello from API Quest!\"}", "The server echoes your message back"],
         "/api/v1/sandbox/stream", None),
        ("Listen and Respond", "Connect to the quiz WebSocket and answer the multiplication question within 5 seconds.", "GET", "/api/v1/sandbox/stream/quiz", None, None, None, 150,
         ["Connect via WebSocket to /stream/quiz", "The server sends a multiplication question", "You have 5 seconds to answer", "Send {\"answer\": <number>}", "Calculate and respond quickly"],
         "/api/v1/sandbox/stream", None),
        ("Server-Sent Events", "Subscribe to price updates.", "GET", "/api/v1/sandbox/stream/prices", {"Accept": "text/event-stream"}, None, None, 150,
         ["SSE uses regular HTTP GET", "Set Accept: text/event-stream", "The server pushes events to you", "Events are prefixed with 'data:'", "Unidirectional: server → client"],
         "/api/v1/sandbox/stream", None),
        ("Heartbeat", "Connect to the heartbeat WebSocket and send a ping to keep the connection alive.", "GET", "/api/v1/sandbox/stream/heartbeat", None, None,
         {"type": "ping"}, 150,
         ["The server drops idle connections after 30s", "Send a ping message to stay alive", "{\"type\": \"ping\"}", "Server responds with {\"type\": \"pong\"}", "Connect to /stream/heartbeat"],
         "/api/v1/sandbox/stream", None),
        ("Channel Subscription", "Connect to the channels WebSocket and subscribe to the \"tech\" channel.", "GET", "/api/v1/sandbox/stream/channels", None, None,
         {"action": "subscribe", "channel": "tech"}, 150,
         ["Connect to /stream/channels", "Send a subscribe message", "{\"action\": \"subscribe\", \"channel\": \"tech\"}", "Available channels: sports, tech, finance", "You'll receive channel notifications"],
         "/api/v1/sandbox/stream", None),
    ],
    "System Design": [
        ("Cache It", "Avoid re-downloading data — first GET the expensive data to discover its ETag, then request again with If-None-Match to get a 304.", "GET", "/api/v1/sandbox/advanced/expensive-data",
         {"If-None-Match": '"<etag>"'}, None, None, 200,
         ["GET /api/v1/sandbox/advanced/expensive-data first", "Check the ETag in the response headers", "Use If-None-Match header with that ETag", "304 means data hasn't changed", "Saves bandwidth and processing"],
         "/api/v1/sandbox/advanced", None),
        ("Bulk Operations", 'Create three items ("Item 1", "Item 2", "Item 3") in a single batch request.', "POST", "/api/v1/sandbox/advanced/items/batch",
         {"Content-Type": "application/json"}, None,
         {"items": [{"name": "Item 1"}, {"name": "Item 2"}, {"name": "Item 3"}]}, 200,
         ["POST to /items/batch", "Send an items array", "Each item needs a name", "Max 100 items per batch", "Response shows created count and errors"],
         "/api/v1/sandbox/advanced", None),
        ("Async Processing", "Start an async sales report for period Q1. The response will tell you how to poll for completion.", "POST", "/api/v1/sandbox/advanced/reports",
         {"Content-Type": "application/json"}, None,
         {"type": "sales", "period": "Q1"}, 200,
         ["POST starts the report generation", "202 Accepted means it's processing", "Poll the status URL", "Status: pending → processing → complete", "Download when complete"],
         "/api/v1/sandbox/advanced", None),
        ("Idempotency", 'Process a $99.99 USD payment with idempotency key "unique-request-id-123" to prevent duplicate charges.', "POST", "/api/v1/sandbox/advanced/payments",
         {"Content-Type": "application/json", "Idempotency-Key": "unique-request-id-123"}, None,
         {"amount": 99.99, "currency": "USD"}, 200,
         ["What if a payment request is sent twice?", "Idempotency keys prevent duplicates", "Add Idempotency-Key header", "Same key = same response (no duplicate charge)", "Idempotency-Key: unique-request-id-123"],
         "/api/v1/sandbox/advanced", None),
        ("Webhook Receiver", 'Register a webhook pointing to /api/v1/sandbox/advanced/webhooks/echo that listens for "order.created" events.', "POST", "/api/v1/sandbox/advanced/webhooks/register",
         {"Content-Type": "application/json"}, None,
         {"url": "/api/v1/sandbox/advanced/webhooks/echo", "events": ["order.created"]}, 200,
         ["POST to /webhooks/register", "Body needs url and events fields", "url: /api/v1/sandbox/advanced/webhooks/echo", "events: [\"order.created\"]", "After registering, create an order to test it"],
         "/api/v1/sandbox/advanced", None),
        ("The Circuit Breaker", "Handle a flaky service.", "GET", "/api/v1/sandbox/advanced/flaky-service", None, None, None, 200,
         ["This service fails 50% of the time", "Circuit breakers detect failure patterns", "States: closed → open → half-open", "Closed: requests pass through", "Open: requests are blocked until recovery"],
         "/api/v1/sandbox/advanced", None),
    ],
}


BADGES = [
    {"name": "First Steps", "description": "Complete your first challenge", "criteria_type": "challenge_count", "criteria_value": 1},
    {"name": "REST Rookie", "description": "Complete the REST Fundamentals track", "criteria_type": "track_complete", "criteria_value": 1},
    {"name": "Query Wizard", "description": "Complete the Query Mastery track", "criteria_type": "track_complete", "criteria_value": 1},
    {"name": "Auth Master", "description": "Complete the Auth & Security track", "criteria_type": "track_complete", "criteria_value": 1},
    {"name": "Data Explorer", "description": "Complete the Data Relationships track", "criteria_type": "track_complete", "criteria_value": 1},
    {"name": "Bug Hunter", "description": "Solve 5 Error Detective challenges", "criteria_type": "challenge_count_in_track", "criteria_value": 5},
    {"name": "Real-Time Pro", "description": "Complete the Real-Time APIs track", "criteria_type": "track_complete", "criteria_value": 1},
    {"name": "System Architect", "description": "Complete the System Design track", "criteria_type": "track_complete", "criteria_value": 1},
    {"name": "Speed Demon", "description": "Solve 3 challenges under the time limit", "criteria_type": "speed_solves", "criteria_value": 3},
    {"name": "Streak Champion", "description": "Maintain a 7-day streak", "criteria_type": "streak", "criteria_value": 7},
    {"name": "Perfectionist", "description": "Solve 10 challenges on first attempt", "criteria_type": "first_attempt_solves", "criteria_value": 10},
    {"name": "Track Titan", "description": "Complete all tracks", "criteria_type": "all_tracks_complete", "criteria_value": 7},
    {"name": "Beginner Graduate", "description": "Complete all Beginner tier challenges", "criteria_type": "tier_complete", "criteria_value": 14},
    {"name": "Intermediate Graduate", "description": "Complete all Intermediate tier challenges", "criteria_type": "tier_complete", "criteria_value": 14},
    {"name": "Advanced Graduate", "description": "Complete all Advanced tier challenges", "criteria_type": "tier_complete", "criteria_value": 13},
    {"name": "Quest Master", "description": "Complete every challenge in the game", "criteria_type": "all_challenges_complete", "criteria_value": 47},
]


def seed_database(db: Session) -> None:
    """Populate tracks, challenges, and badges (upsert — safe to re-run).

    Matches existing rows by title/name and updates their content fields
    while preserving primary-key UUIDs.  This keeps foreign-key references
    from submissions, hint_reveals, user_track_progress, and user_badges
    intact so player progress is never lost on reseed.
    """
    created_tracks = updated_tracks = 0
    created_challenges = updated_challenges = 0
    created_badges = updated_badges = 0

    # ── Upsert tracks ──────────────────────────────────────────────
    track_objects: dict[str, Track] = {}
    for t in TRACKS:
        existing = db.query(Track).filter_by(title=t["title"]).first()
        if existing:
            existing.description = t["description"]
            existing.difficulty = t["difficulty"]
            existing.order_index = t["order_index"]
            track_objects[t["title"]] = existing
            updated_tracks += 1
        else:
            track = Track(**t)
            db.add(track)
            db.flush()
            track_objects[t["title"]] = track
            created_tracks += 1

    db.flush()

    # ── Upsert challenges ──────────────────────────────────────────
    for track_title, challenges in CHALLENGES.items():
        track = track_objects[track_title]
        for idx, c in enumerate(challenges):
            title, desc, method, path, headers, query, body, points, hints, sandbox, time_limit = c
            existing = (
                db.query(Challenge)
                .filter_by(track_id=track.id, title=title)
                .first()
            )
            if existing:
                existing.description = desc
                existing.difficulty = track.difficulty
                existing.points_value = points
                existing.expected_method = method
                existing.expected_path = path
                existing.expected_headers = headers
                existing.expected_query_params = query
                existing.expected_body = body
                existing.hints = hints
                existing.order_index = idx + 1
                existing.sandbox_endpoint = sandbox
                existing.time_limit_seconds = time_limit
                updated_challenges += 1
            else:
                challenge = Challenge(
                    track_id=track.id,
                    title=title,
                    description=desc,
                    difficulty=track.difficulty,
                    points_value=points,
                    expected_method=method,
                    expected_path=path,
                    expected_headers=headers,
                    expected_query_params=query,
                    expected_body=body,
                    hints=hints,
                    order_index=idx + 1,
                    sandbox_endpoint=sandbox,
                    time_limit_seconds=time_limit,
                )
                db.add(challenge)
                created_challenges += 1

    # ── Upsert badges ─────────────────────────────────────────────
    for b in BADGES:
        existing = db.query(Badge).filter_by(name=b["name"]).first()
        if existing:
            existing.description = b["description"]
            existing.criteria_type = b["criteria_type"]
            existing.criteria_value = b["criteria_value"]
            updated_badges += 1
        else:
            badge = Badge(**b)
            db.add(badge)
            created_badges += 1

    db.commit()

    total_new = created_tracks + created_challenges + created_badges
    total_upd = updated_tracks + updated_challenges + updated_badges
    if total_new and total_upd:
        print(
            f"Seed: created {created_tracks}t/{created_challenges}c/{created_badges}b, "
            f"updated {updated_tracks}t/{updated_challenges}c/{updated_badges}b."
        )
    elif total_upd:
        print(f"Seed data up-to-date ({updated_tracks} tracks, {updated_challenges} challenges, {updated_badges} badges).")
    else:
        print(f"Seeded {created_tracks} tracks, {created_challenges} challenges, {created_badges} badges.")


if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_database(db)
