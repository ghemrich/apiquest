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
        ("Status Code Detective", "Match HTTP status codes to three error scenarios: a missing resource, a bad request, and a wrong method. Submit them as an ordered array.", "POST", "/api/v1/sandbox/books/status-check", None, None,
         {"codes": [404, 400, 405]}, 75,
         ["What status code means Not Found?", "What about Bad Request?", "Method Not Allowed is which code?", "404, 400, 405", "POST to /status-check with {\"codes\": [404, 400, 405]}"],
         "/api/v1/sandbox/books", None),
        ("The Content-Type Mystery", 'Set the correct Content-Type header and POST a book titled "Test Book" by "Test Author" (2026).', "POST", "/api/v1/sandbox/books/", {"Content-Type": "application/json"}, None,
         {"title": "Test Book", "author": "Test Author", "year": 2026}, 75,
         ["APIs need to know what format you're sending", "The header name is Content-Type", "JSON content type is application/json", "Include it in headers", 'POST /api/v1/sandbox/books/ with Content-Type: application/json and {"title": "Test Book", "author": "Test Author", "year": 2026}'],
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
        ("Cascade Effects", "Delete a project and observe cascading.", "DELETE", "/api/v1/sandbox/users-data/projects/3", None, None, None, 100,
         ["DELETE removes the resource", "What happens to child resources?", "Tasks belong to the project", "Cascade delete removes children too", "DELETE /api/v1/sandbox/users-data/projects/3"],
         "/api/v1/sandbox/users-data", None),
    ],
    "Error Detective": [
        ("The Silent Failure", "Fix the typo in the query param.", "GET", "/api/v1/sandbox/broken/items", None, {"status": "active"}, None, 150,
         ["The API has a subtle bug", "Check what happens with staus vs status", "One is a typo that silently fails", "Use the correct spelling: status", "?status=active with correct spelling"],
         "/api/v1/sandbox/broken", None),
        ("The Wrong Method", 'Update item 42 with name "Updated Item" and status "active" — not every write uses POST.', "PUT", "/api/v1/sandbox/broken/items/42", {"Content-Type": "application/json"}, None,
         {"name": "Updated Item", "status": "active"}, 150,
         ["POST returns 405 Method Not Allowed", "Which method is for updates?", "PUT replaces the resource", "Content-Type: application/json", "PUT /api/v1/sandbox/broken/items/42"],
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
        ("Race Condition", "Use ETags for safe updates.", "PUT", "/api/v1/sandbox/broken/documents/1",
         {"If-Match": '"<etag>"', "Content-Type": "application/json"}, None,
         {"title": "Updated Document"}, 150,
         ["GET the document first to get the ETag", "Use If-Match header with the ETag", "This prevents race conditions", "412 means your ETag is stale", "PUT with If-Match: \"<etag>\""],
         "/api/v1/sandbox/broken", None),
        ("The Broken Chain", "Complete a 3-step API chain.", "GET", "/api/v1/sandbox/broken/step1", None, None, None, 150,
         ["Step 1 gives you a token", "Step 2 uses that token", "Step 3 uses the ID from step 2", "Tokens expire in 30 seconds", "GET /step1 → /step2?token=X → /step3/{id}"],
         "/api/v1/sandbox/broken", None),
    ],
    "Real-Time APIs": [
        ("Your First WebSocket", 'Connect to the chat WebSocket and send "Hello from API Quest!".', "GET", "ws://host/api/v1/sandbox/stream/chat", None, None,
         {"text": "Hello from API Quest!"}, 150,
         ["WebSockets use ws:// protocol", "Connect to /stream/chat", "Send a JSON message", "{\"text\": \"Hello from API Quest!\"}", "The server echoes your message back"],
         "/api/v1/sandbox/stream", None),
        ("Listen and Respond", "Answer a math quiz in time.", "GET", "ws://host/api/v1/sandbox/stream/quiz", None, None, None, 150,
         ["Connect and wait for a question", "You have 5 seconds to answer", "Send {\"answer\": <number>}", "It's a multiplication question", "Calculate and respond quickly"],
         "/api/v1/sandbox/stream", None),
        ("Server-Sent Events", "Subscribe to price updates.", "GET", "/api/v1/sandbox/stream/prices", {"Accept": "text/event-stream"}, None, None, 150,
         ["SSE uses regular HTTP GET", "Set Accept: text/event-stream", "The server pushes events to you", "Events are prefixed with 'data:'", "Unidirectional: server → client"],
         "/api/v1/sandbox/stream", None),
        ("Heartbeat", "Keep a WebSocket connection alive.", "GET", "ws://host/api/v1/sandbox/stream/heartbeat", None, None, None, 150,
         ["The server drops idle connections", "Send ping messages to stay alive", "{\"type\": \"ping\"}", "Every 15 seconds", "Server responds with {\"type\": \"pong\"}"],
         "/api/v1/sandbox/stream", None),
        ("Channel Subscription", "Subscribe to a channel.", "GET", "ws://host/api/v1/sandbox/stream/channels", None, None,
         {"action": "subscribe", "channel": "tech"}, 150,
         ["Connect to /stream/channels", "Send a subscribe message", "{\"action\": \"subscribe\", \"channel\": \"tech\"}", "Channels: sports, tech, finance", "You'll receive channel notifications"],
         "/api/v1/sandbox/stream", None),
    ],
    "System Design": [
        ("Cache It", "Use ETags for conditional requests.", "GET", "/api/v1/sandbox/advanced/expensive-data",
         {"If-None-Match": '"<etag>"'}, None, None, 200,
         ["GET the data first to see the ETag", "Use If-None-Match header", "304 means data hasn't changed", "Saves bandwidth and processing", "If-None-Match: \"<etag>\""],
         "/api/v1/sandbox/advanced", None),
        ("Bulk Operations", 'Create three items ("Item 1", "Item 2", "Item 3") in a single batch request.', "POST", "/api/v1/sandbox/advanced/items/batch",
         {"Content-Type": "application/json"}, None,
         {"items": [{"name": "Item 1"}, {"name": "Item 2"}, {"name": "Item 3"}]}, 200,
         ["POST to /items/batch", "Send an items array", "Each item needs a name", "Max 100 items per batch", "Response shows created count and errors"],
         "/api/v1/sandbox/advanced", None),
        ("Async Processing", "Start an async sales report for period Q1 and learn how to poll for its completion.", "POST", "/api/v1/sandbox/advanced/reports",
         {"Content-Type": "application/json"}, None,
         {"type": "sales", "period": "Q1"}, 200,
         ["POST starts the report generation", "202 Accepted means it's processing", "Poll the status URL", "Status: pending → processing → complete", "Download when complete"],
         "/api/v1/sandbox/advanced", None),
        ("Idempotency", 'Process a $99.99 USD payment with idempotency key "unique-request-id-123" to prevent duplicate charges.', "POST", "/api/v1/sandbox/advanced/payments",
         {"Content-Type": "application/json", "Idempotency-Key": "unique-request-id-123"}, None,
         {"amount": 99.99, "currency": "USD"}, 200,
         ["What if a payment request is sent twice?", "Idempotency keys prevent duplicates", "Add Idempotency-Key header", "Same key = same response (no duplicate charge)", "Idempotency-Key: unique-request-id-123"],
         "/api/v1/sandbox/advanced", None),
        ("Webhook Receiver", 'Register a webhook at the echo endpoint to listen for "order.created" events.', "POST", "/api/v1/sandbox/advanced/webhooks/register",
         {"Content-Type": "application/json"}, None,
         {"url": "/api/v1/sandbox/advanced/webhooks/echo", "events": ["order.created"]}, 200,
         ["Register a webhook URL first", "POST to /webhooks/register", "Listen for order.created events", "Then create an order to trigger it", "Check /webhooks/echo/received"],
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
    """Populate tracks, challenges, and badges if they don't exist yet."""

    # Skip if already seeded
    if db.query(Track).first():
        print("Database already seeded — skipping.")
        return

    # Create tracks
    track_objects: dict[str, Track] = {}
    for t in TRACKS:
        track = Track(**t)
        db.add(track)
        db.flush()
        track_objects[t["title"]] = track

    # Create challenges
    for track_title, challenges in CHALLENGES.items():
        track = track_objects[track_title]
        for idx, c in enumerate(challenges):
            title, desc, method, path, headers, query, body, points, hints, sandbox, time_limit = c
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

    # Create badges
    for b in BADGES:
        badge = Badge(**b)
        db.add(badge)

    db.commit()
    print(f"Seeded {len(TRACKS)} tracks, {sum(len(c) for c in CHALLENGES.values())} challenges, {len(BADGES)} badges.")


if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_database(db)
