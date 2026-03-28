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


# Challenges per track.
# Each entry: (title, desc, method, path, headers, query, body, points, clues, hints, sandbox, time_limit)
CHALLENGES = {
    "REST Fundamentals": [
        ("Hello, API", "Make your first API request.", "GET", "/api/v1/sandbox/hello/", None, None, None, 50,
         ["Every API journey starts with a simple greeting.", "The sandbox has a /hello endpoint waiting for visitors.", "Think about which HTTP method is used to read data."],
         ["What's the simplest HTTP request?", "No body, no headers needed", "Try the /hello endpoint", "GET /api/v1/sandbox/hello/", "Just send a GET request"],
         "/api/v1/sandbox/hello", 120),
        ("The Library", "Retrieve the list of all books.", "GET", "/api/v1/sandbox/books/", None, None, None, 50,
         ["The sandbox has a books collection waiting to be explored.", "REST APIs use plural nouns for collections.", "No parameters needed for a full listing."],
         ["Books are at the /books endpoint", "No query params needed", "Just a simple GET", "GET /api/v1/sandbox/books/", "Returns a paginated list of books"],
         "/api/v1/sandbox/books", 120),
        ("Specific Retrieval", 'Fetch the book "Design Patterns" by its ID.', "GET", "/api/v1/sandbox/books/3", None, None, None, 50,
         ["You'll need to know the book's ID — try listing all books first.", "REST APIs address individual resources with a path parameter.", "The path follows the pattern /collection/{id}."],
         ["List all books to find its ID", "REST APIs use path parameters like /resource/{id}", "The book ID is 3", "GET /api/v1/sandbox/books/3", "Full path: GET /api/v1/sandbox/books/3"],
         "/api/v1/sandbox/books", 120),
        ("Adding to the Shelf", 'Add the book "Clean Code" by Robert C. Martin (2008) to the collection using POST.',
         "POST", "/api/v1/sandbox/books/", {"Content-Type": "application/json"}, None,
         {"title": "Clean Code", "author": "Robert C. Martin", "year": 2008}, 50,
         ["Creating a new resource requires a different HTTP method than reading.", "The server needs to know the format of your data — check the Content-Type header.", "Book records have three fields: title, author, and year."],
         ["POST is the HTTP method for creating resources", "You need a Content-Type: application/json header",
          "The body is JSON with title, author, and year", 'Try: {"title": "Clean Code", "author": "Robert C. Martin", "year": 2008}',
          "POST /api/v1/sandbox/books/ with the JSON body"],
         "/api/v1/sandbox/books", None),
        ("Fix the Typo", 'Book 4 has a misspelled author name. Use PUT to fix it.',
         "PUT", "/api/v1/sandbox/books/4", {"Content-Type": "application/json"}, None,
         {"title": "Refactoring", "author": "Martin Fowler", "year": 2018}, 50,
         ["Start by reading book 4 to see what's wrong.", "PUT replaces the entire resource — you need to send all fields, not just the fix.", "Look carefully at the author's name in the current data."],
         ["First GET /api/v1/sandbox/books/4 to see the current data", "Look carefully at the author name",
          "PUT replaces the entire resource — send all fields", "Content-Type must be application/json",
          'PUT /api/v1/sandbox/books/4 with {"title": "Refactoring", "author": "Martin Fowler", "year": 2018}'],
         "/api/v1/sandbox/books", None),
        ("Clearing the Shelf", 'There\'s a placeholder test book cluttering the library. List all the books to find it, then delete it.', "DELETE", "/api/v1/sandbox/books/99", None, None, None, 50,
         ["Browse the collection — one book clearly doesn't belong.", "HTTP has a method specifically for removing resources.", "No request body or special headers are needed for this operation."],
         ["GET /api/v1/sandbox/books/ and look for a book that doesn't belong", "Which HTTP method removes resources?", "The placeholder book has an obvious title", "DELETE /api/v1/sandbox/books/99", "No body or headers needed"],
         "/api/v1/sandbox/books", 120),
        ("Status Code Detective", 'Trigger three errors on the books API and observe the status codes: (1) request a book that doesn\'t exist, (2) POST an invalid body, (3) try PATCH on /books/1. Then POST your findings as {"codes": [code1, code2, code3]} to /api/v1/sandbox/books/status-check — the endpoint will tell you which answers are correct.', "POST", "/api/v1/sandbox/books/status-check", None, None,
         {"codes": [404, 400, 405]}, 75,
         ["Different mistakes trigger different HTTP status codes.", "Try requesting a nonexistent resource, sending bad data, and using an unsupported method.", "The status-check endpoint will tell you which codes are right and which are wrong."],
         ["Try GET /api/v1/sandbox/books/99999 — what status code do you get?", "Try POSTing garbage to /api/v1/sandbox/books/", "Try PATCH /api/v1/sandbox/books/1", "The three codes are 404, 400, and 405", "POST {\"codes\": [404, 400, 405]} to /api/v1/sandbox/books/status-check"],
         "/api/v1/sandbox/books", None),
    ],
    "Query Mastery": [
        ("Filter by Status", "Retrieve only the tasks that have been completed.", "GET", "/api/v1/sandbox/tasks/", None, {"status": "completed"}, None, 50,
         ["Query parameters let you narrow down results without changing the endpoint.", "The tasks API supports filtering by task state.", "Append a key=value pair after a ? in the URL."],
         ["Use a query parameter", "The parameter name is status", "completed is one valid status", "?status=completed", "GET /api/v1/sandbox/tasks/?status=completed"],
         "/api/v1/sandbox/tasks", 120),
        ("Page Turner", "Use pagination to fetch page 3 with 10 items per page.", "GET", "/api/v1/sandbox/tasks/", None, {"page": "3", "per_page": "10"}, None, 50,
         ["Large collections are split into pages.", "Two parameters control pagination: which page and how many items per page.", "Combine both parameters with & in the URL."],
         ["Pagination uses page and per_page", "page=3 gets the third page", "per_page controls items per page", "?page=3&per_page=10", "Combine both parameters"],
         "/api/v1/sandbox/tasks", None),
        ("Sort It Out", "Sort tasks by creation date descending.", "GET", "/api/v1/sandbox/tasks/", None, {"sort": "-created_at"}, None, 50,
         ["APIs often support sorting via a query parameter.", "A prefix character can indicate ascending vs descending order.", "You want the newest items first."],
         ["The sort parameter controls ordering", "Prefix with - for descending", "Sort by created_at field", "?sort=-created_at", "Minus means newest first"],
         "/api/v1/sandbox/tasks", 120),
        ("Search Party", 'Search for tasks containing the keyword "database".', "GET", "/api/v1/sandbox/tasks/", None, {"search": "database"}, None, 50,
         ["The tasks endpoint supports text search across titles.", "Search is a query parameter like any other filter.", "The matching is case-insensitive."],
         ["There's a search parameter", "It does partial string matching", "Search for 'database'", "?search=database", "Case-insensitive search"],
         "/api/v1/sandbox/tasks", None),
        ("Combining Powers", 'Combine filtering, searching, sorting, and pagination: find completed tasks matching "API", sorted by priority descending, page 2 with 5 per page.', "GET", "/api/v1/sandbox/tasks/", None,
         {"status": "completed", "search": "API", "sort": "-priority", "page": "2", "per_page": "5"}, None, 75,
         ["All the query parameters you've learned can be used together in one request.", "Chain multiple parameters with & — order doesn't matter.", "You need five parameters: one each for status, search, sort, page, and page size."],
         ["Combine status, search, sort, and pagination", "status=completed&search=API", "Add sort=-priority", "page=2&per_page=5", "Chain all 5 parameters with &"],
         "/api/v1/sandbox/tasks", None),
        ("Field Selection", "Request only the title and status fields from the tasks endpoint.", "GET", "/api/v1/sandbox/tasks/", None, {"fields": "title,status"}, None, 75,
         ["APIs sometimes let you choose which fields appear in the response.", "This reduces payload size — useful for bandwidth-constrained clients.", "Provide the desired field names as a comma-separated list."],
         ["The fields parameter selects which data to return", "Comma-separated list of field names", "fields=title,status", "Only title and status columns", "Sparse fieldsets reduce payload size"],
         "/api/v1/sandbox/tasks", None),
    ],
    "Auth & Security": [
        ("The Locked Door", "Log in with username player1 and password quest123 to receive an access token.", "POST", "/api/v1/sandbox/mock-auth/login", {"Content-Type": "application/json"}, None,
         {"username": "player1", "password": "quest123"}, 100,
         ["Authentication starts with exchanging credentials for a token.", "The login endpoint expects your credentials as a JSON body.", "You need both a username and password to authenticate."],
         ["POST to the login endpoint", "Send credentials as JSON", "Username is player1", "Password is quest123", "Content-Type: application/json"],
         "/api/v1/sandbox/mock-auth", None),
        ("Bearer of Tokens", 'The /profile endpoint returns your user info — but it\'s protected. First get a token from /login (see The Locked Door), then use it to authenticate.', "GET", "/api/v1/sandbox/mock-auth/profile", {"Authorization": "Bearer <access_token>"}, None, None, 100,
         ["Protected endpoints reject unauthenticated requests — try it and read the error.", "Tokens travel in a specific HTTP header with a specific prefix.", "You'll need to complete The Locked Door first to get a token."],
         ["Try GET /profile without auth — read the error", "The Authorization header carries your token", "Format: Bearer <your_token>", "Authorization: Bearer <your_token>", "Get a token from /login first"],
         "/api/v1/sandbox/mock-auth", None),
        ("Token Expired", 'Access tokens don\'t last forever. When /profile returns 401 "Token expired", use the refresh_token you received from /login to get a new access token without logging in again.', "POST", "/api/v1/sandbox/mock-auth/refresh", {"Content-Type": "application/json"}, None,
         {"refresh_token": "<refresh_token>"}, 100,
         ["Access tokens are intentionally short-lived for security.", "The login response gave you a second token specifically for renewal.", "There's a dedicated endpoint for getting a fresh access token."],
         ["Wait for your access token to expire (60s) or just try the refresh flow", "POST to /refresh with your refresh_token", "Send {\"refresh_token\": \"<your_refresh_token>\"}", "You got the refresh_token from /login", "Content-Type: application/json"],
         "/api/v1/sandbox/mock-auth", None),
        ("Role Play", 'The /admin/users endpoint lists all users — but it\'s restricted. Try accessing it with your player1 token and read the error. You\'ll need to find different credentials. Check GET /accounts for available test accounts.', "GET", "/api/v1/sandbox/mock-auth/admin/users", {"Authorization": "Bearer <admin_token>"}, None, None, 100,
         ["Not all authenticated users have the same permissions.", "The error message reveals what role you need.", "The API has a discovery endpoint that lists available test accounts."],
         ["Try with player1's token — what does the 403 tell you?", "GET /api/v1/sandbox/mock-auth/accounts lists test accounts", "You need an admin account", "Password: adminquest123", "Authorization: Bearer <admin_token>"],
         "/api/v1/sandbox/mock-auth", None),
        ("API Key vs Token", 'The /external/data endpoint uses a different auth mechanism than Bearer tokens. Try accessing it — the error will tell you what it expects. Then visit the endpoint it suggests to get a key.', "GET", "/api/v1/sandbox/mock-auth/external/data", {"X-API-Key": "sk_test_abc123xyz"}, None, None, 100,
         ["Not all APIs use Bearer tokens for authentication.", "The error response is your best friend — it explains exactly what's expected.", "There's an endpoint where you can retrieve the credentials you need."],
         ["Try GET /external/data without auth — read the error", "This endpoint doesn't use Bearer tokens", "The error tells you which header and where to get a key", "GET /api/v1/sandbox/mock-auth/api-keys to get a test key", "Use the X-API-Key header with the key you received"],
         "/api/v1/sandbox/mock-auth", None),
        ("Rate Limited", 'The /limited endpoint has rate limiting. Hit it a few times with your Bearer token and study the response headers carefully — then report what you found to /rate-limit-report.', "POST", "/api/v1/sandbox/mock-auth/rate-limit-report", {"Content-Type": "application/json"}, None,
         {"limit": 5, "window_seconds": 60}, 100,
         ["APIs often limit how many requests you can make in a time window.", "The response headers contain metadata about the rate limit policy.", "You need to report two numbers: the request limit and the time window."],
         ["GET /limited with your Bearer token and check response headers", "Look for X-RateLimit-Limit and Retry-After headers", "X-RateLimit-Limit shows max requests per window", "Retry-After tells the window length in seconds", "POST your findings to /rate-limit-report"],
         "/api/v1/sandbox/mock-auth", None),
    ],
    "Data Relationships": [
        ("Nested Resources", "Retrieve all projects belonging to user 7.", "GET", "/api/v1/sandbox/users-data/7/projects", None, None, None, 100,
         ["REST APIs model ownership by nesting resources under their parent.", "The URL structure reflects the relationship: parent/id/children.", "Start from the users-data endpoint and navigate to a specific user's projects."],
         ["Resources can be nested under others", "User 7 has projects", "/users-data/{user_id}/projects", "GET request, no body needed", "GET /api/v1/sandbox/users-data/7/projects"],
         "/api/v1/sandbox/users-data", None),
        ("Deep Nesting", "Retrieve all tasks for project 3 of user 7.", "GET", "/api/v1/sandbox/users-data/7/projects/3/tasks", None, None, None, 100,
         ["Resource nesting can go multiple levels deep.", "Follow the ownership chain: who owns the project, and what does the project contain?", "Each level in the URL adds another /resource/{id} segment."],
         ["Go deeper: user → project → tasks", "Three levels of nesting", "User 7, Project 3", "/7/projects/3/tasks", "GET /api/v1/sandbox/users-data/7/projects/3/tasks"],
         "/api/v1/sandbox/users-data", None),
        ("Include Related Data", "Use eager loading to include tasks.", "GET", "/api/v1/sandbox/users-data/projects/3", None, {"include": "tasks"}, None, 100,
         ["Instead of making two requests, some APIs let you embed related data in one call.", "A query parameter can tell the API to bundle child resources into the response.", "Try fetching project 3 and asking for its tasks in the same response."],
         ["The include parameter embeds related data", "include=tasks adds tasks to the response", "Alternative to nested resource URLs", "?include=tasks", "GET /projects/3?include=tasks"],
         "/api/v1/sandbox/users-data", None),
        ("Creating with Relationships", 'Create a new high-priority task titled "Write unit tests" linked to project 3.', "POST", "/api/v1/sandbox/users-data/tasks", None, None,
         {"title": "Write unit tests", "project_id": 3, "priority": "high"}, 100,
         ["New resources are created with a POST request.", "The task needs to know which project it belongs to — use a foreign key.", "The request body should include all required fields: title, project link, and priority."],
         ["POST to create a new task", "Link it to project 3 via project_id", "Include title and priority", "project_id: 3", "POST /api/v1/sandbox/users-data/tasks"],
         "/api/v1/sandbox/users-data", None),
        ("Many-to-Many", "Add user 5 to team 2.", "POST", "/api/v1/sandbox/users-data/teams/2/members", None, None,
         {"user_id": 5}, 100,
         ["Users can belong to multiple teams, and teams have multiple users.", "Adding a member is a POST to the team's member list.", "The body identifies which user to add."],
         ["Teams and users are many-to-many", "POST to add a member", "/teams/2/members", "Send user_id in body", "POST with {\"user_id\": 5}"],
         "/api/v1/sandbox/users-data", None),
        ("Cascade Effects", 'Delete project 3 and observe what happens to its tasks. Warning: this is destructive — complete the other Data Relationships challenges first! Check the tasks before and after.', "DELETE", "/api/v1/sandbox/users-data/projects/3", None, None, None, 100,
         ["Deleting a parent resource can affect its children — check what exists before and after.", "There's an HTTP method specifically for removing resources.", "This is destructive and cannot be undone — make sure you've completed the other challenges first."],
         ["First GET /projects/3?include=tasks to see what exists", "DELETE removes the resource", "What happens to child resources?", "Cascade delete removes children too", "DELETE /api/v1/sandbox/users-data/projects/3"],
         "/api/v1/sandbox/users-data", None),
    ],
    "Error Detective": [
        ("The Silent Failure", "Fix the typo in the query param.", "GET", "/api/v1/sandbox/broken/items", None, {"status": "active"}, None, 150,
         ["This API has a subtle query parameter bug that fails silently.", "Try filtering items and compare the results — does the filter actually work?", "Spelling mistakes in parameter names don't cause errors; they just get ignored."],
         ["The API has a subtle bug", "Check what happens with staus vs status", "One is a typo that silently fails", "Use the correct spelling: status", "?status=active with correct spelling"],
         "/api/v1/sandbox/broken", None),
        ("Missing Required Fields", 'Create an order for a "Widget" (quantity: 5) shipped to "123 Main St". The API will tell you if anything is missing.', "POST", "/api/v1/sandbox/broken/orders", None, None,
         {"product": "Widget", "quantity": 5, "shipping_address": "123 Main St"}, 150,
         ["The orders API validates all required fields and reports what's missing.", "Pay close attention to 422 error responses — they list each missing field.", "An order needs product details, a quantity, and a destination."],
         ["Read the 422 error carefully", "It tells you which field is missing", "shipping_address is required", "Include product, quantity, and shipping_address", "All three fields are mandatory"],
         "/api/v1/sandbox/broken", None),
        ("The Encoding Trap", 'Search for "hello world" — but watch out for how spaces travel in URLs.', "GET", "/api/v1/sandbox/broken/search", None, {"q": "hello world"}, None, 150,
         ["URLs cannot contain literal space characters.", "There's a standard way to represent special characters in URLs.", "Most HTTP clients handle this automatically, but it's good to understand what happens."],
         ["Spaces in URLs need encoding", "%20 or + replaces spaces", "q=hello%20world", "URL encoding is essential", "The query is 'hello world'"],
         "/api/v1/sandbox/broken", None),
        ("Version Mismatch", 'GET product 1 from the products API. The response will tell you something is off — follow the hint to find the better version.', "GET", "/api/v1/sandbox/broken/v2/products/1", None, None, None, 150,
         ["Real APIs evolve over time and often maintain multiple versions.", "Start by trying the v1 endpoint and read the full response carefully.", "Deprecation notices in API responses point you to the newer version."],
         ["Start with GET /api/v1/sandbox/broken/v1/products/1", "Read the response carefully — is there a deprecation notice?", "v2 has additional fields like description and category", "Use /v2/ instead of /v1/", "GET /api/v1/sandbox/broken/v2/products/1"],
         "/api/v1/sandbox/broken", None),
        ("The Timeout", "Add a limit to avoid timeout.", "GET", "/api/v1/sandbox/broken/heavy-data", None, {"limit": "50"}, None, 150,
         ["This endpoint returns a massive dataset that overwhelms the server.", "The 504 error message contains a hint about how to fix it.", "You can control how much data the server returns."],
         ["Without a limit, the request times out", "504 means Gateway Timeout", "Add a limit parameter", "Keep it under 100", "?limit=50"],
         "/api/v1/sandbox/broken", None),
        ("Race Condition", "Safely update document 1 using its ETag — first GET the document to discover the current ETag, then PUT with If-Match.", "PUT", "/api/v1/sandbox/broken/documents/1",
         {"If-Match": '"<etag>"', "Content-Type": "application/json"}, None,
         {"title": "Updated Document"}, 150,
         ["Concurrent edits can overwrite each other — ETags prevent that.", "First read the document to discover its current version identifier.", "Your update request must prove it's working with the latest version."],
         ["GET /api/v1/sandbox/broken/documents/1 to get the ETag", "The ETag is in the response headers", "Use If-Match header with the ETag value", "412 means your ETag is stale", "PUT with If-Match and Content-Type: application/json"],
         "/api/v1/sandbox/broken", None),
        ("The Broken Chain", 'Follow a 3-step API chain: each step gives you data needed for the next. Start with GET /api/v1/sandbox/broken/step1 and follow the instructions through all three steps. When you reach the end, submit the final answer to /chain-complete.', "POST", "/api/v1/sandbox/broken/chain-complete", {"Content-Type": "application/json"}, None,
         {"answer": "api-quest-complete"}, 150,
         ["This is a multi-step process — each endpoint returns data and instructions for the next.", "Start at step1 and follow the breadcrumbs.", "The final step asks you to POST an answer — you'll get it by completing the chain."],
         ["GET /api/v1/sandbox/broken/step1 to begin", "Each step tells you where to go next", "Step 2 needs the token from step 1", "Step 3 needs the ID from step 2", "POST the final answer to /chain-complete"],
         "/api/v1/sandbox/broken", None),
    ],
    "Real-Time APIs": [
        ("Your First WebSocket", 'Connect to the chat WebSocket and send "Hello from API Quest!".', "GET", "/api/v1/sandbox/stream/chat", None, None,
         {"text": "Hello from API Quest!"}, 150,
         ["WebSockets are a different protocol than HTTP — they enable two-way communication.", "You need a WebSocket client (wscat, websocat, or a library) to connect.", "Once connected, send your message as a JSON object."],
         ["WebSockets use ws:// protocol", "Connect to /stream/chat", "Send a JSON message", "{\"text\": \"Hello from API Quest!\"}", "The server echoes your message back"],
         "/api/v1/sandbox/stream", None),

        ("Server-Sent Events", "Subscribe to price updates.", "GET", "/api/v1/sandbox/stream/prices", {"Accept": "text/event-stream"}, None, None, 150,
         ["SSE uses regular HTTP but keeps the connection open for the server to push data.", "Unlike WebSockets, SSE is one-way: server to client only.", "You need to tell the server you want a stream, not a regular response."],
         ["SSE uses regular HTTP GET", "Set Accept: text/event-stream", "The server pushes events to you", "Events are prefixed with 'data:'", "Unidirectional: server → client"],
         "/api/v1/sandbox/stream", None),
        ("Heartbeat", "Connect to the heartbeat WebSocket and send a ping to keep the connection alive.", "GET", "/api/v1/sandbox/stream/heartbeat", None, None,
         {"type": "ping"}, 150,
         ["Servers often disconnect idle WebSocket clients after a timeout.", "You need to periodically signal that you're still there.", "The message you send should indicate its purpose via a type field."],
         ["The server drops idle connections after 30s", "Send a ping message to stay alive", "{\"type\": \"ping\"}", "Server responds with {\"type\": \"pong\"}", "Connect to /stream/heartbeat"],
         "/api/v1/sandbox/stream", None),
        ("Channel Subscription", "Connect to the channels WebSocket and subscribe to the \"tech\" channel.", "GET", "/api/v1/sandbox/stream/channels", None, None,
         {"action": "subscribe", "channel": "tech"}, 150,
         ["This WebSocket supports multiple topic channels you can opt into.", "Send a message telling the server what you want to do and which channel.", "Three channels are available: sports, tech, and finance."],
         ["Connect to /stream/channels", "Send a subscribe message", "{\"action\": \"subscribe\", \"channel\": \"tech\"}", "Available channels: sports, tech, finance", "You'll receive channel notifications"],
         "/api/v1/sandbox/stream", None),
    ],
    "System Design": [
        ("Cache It", "Avoid re-downloading data — first GET the expensive data to discover its ETag, then request again with If-None-Match to get a 304.", "GET", "/api/v1/sandbox/advanced/expensive-data",
         {"If-None-Match": '"<etag>"'}, None, None, 200,
         ["HTTP caching lets clients avoid re-downloading unchanged data.", "The first response contains a version fingerprint in the headers.", "On subsequent requests, send that fingerprint so the server can confirm nothing changed."],
         ["GET /api/v1/sandbox/advanced/expensive-data first", "Check the ETag in the response headers", "Use If-None-Match header with that ETag", "304 means data hasn't changed", "Saves bandwidth and processing"],
         "/api/v1/sandbox/advanced", None),
        ("Bulk Operations", 'Create three items ("Item 1", "Item 2", "Item 3") in a single batch request.', "POST", "/api/v1/sandbox/advanced/items/batch",
         {"Content-Type": "application/json"}, None,
         {"items": [{"name": "Item 1"}, {"name": "Item 2"}, {"name": "Item 3"}]}, 200,
         ["Sending one request with multiple items is faster than three separate requests.", "The batch endpoint expects an array of items in the body.", "Each item must include at least a name field."],
         ["POST to /items/batch", "Send an items array", "Each item needs a name", "Max 100 items per batch", "Response shows created count and errors"],
         "/api/v1/sandbox/advanced", None),
        ("Async Processing", 'Start an async sales report for Q1, poll until complete, download the result, and submit the total revenue to /report-check. The API guides you through each step.', "POST", "/api/v1/sandbox/advanced/report-check",
         {"Content-Type": "application/json"}, None,
         {"report_id": "rpt-q1", "total_revenue": 33000}, 200,
         ["Some operations take time — the API acknowledges your request and processes it in the background.", "You'll need to check back periodically to see if the result is ready.", "The final step requires you to do some math on the downloaded data and submit your answer."],
         ["POST {\"type\": \"sales\", \"period\": \"Q1\"} to /reports to start", "202 Accepted — poll the status_url until 'complete'", "GET /reports/{id}/download to fetch the data", "Sum the revenue values from the downloaded data", "POST {\"report_id\": \"rpt-q1\", \"total_revenue\": <sum>} to /report-check"],
         "/api/v1/sandbox/advanced", None),
        ("Idempotency", 'Process a $99.99 USD payment with idempotency key "unique-request-id-123" to prevent duplicate charges.', "POST", "/api/v1/sandbox/advanced/payments",
         {"Content-Type": "application/json", "Idempotency-Key": "unique-request-id-123"}, None,
         {"amount": 99.99, "currency": "USD"}, 200,
         ["What happens if a payment request is accidentally sent twice?", "There's a well-known pattern for ensuring the same request isn't processed more than once.", "A special header carries a unique identifier that ties duplicate requests together."],
         ["What if a payment request is sent twice?", "Idempotency keys prevent duplicates", "Add Idempotency-Key header", "Same key = same response (no duplicate charge)", "Idempotency-Key: unique-request-id-123"],
         "/api/v1/sandbox/advanced", None),
        ("Webhook Receiver", 'Register a webhook pointing to /api/v1/sandbox/advanced/webhooks/echo that listens for "order.created" events.', "POST", "/api/v1/sandbox/advanced/webhooks/register",
         {"Content-Type": "application/json"}, None,
         {"url": "/api/v1/sandbox/advanced/webhooks/echo", "events": ["order.created"]}, 200,
         ["Webhooks flip the client-server relationship — the server calls you when something happens.", "You need to tell the server where to send notifications and which events you care about.", "After registering, try creating an order to see the webhook fire."],
         ["POST to /webhooks/register", "Body needs url and events fields", "url: /api/v1/sandbox/advanced/webhooks/echo", "events: [\"order.created\"]", "After registering, create an order to test it"],
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
    {"name": "Beginner Graduate", "description": "Complete all Beginner tier challenges", "criteria_type": "tier_complete", "criteria_value": 13},
    {"name": "Intermediate Graduate", "description": "Complete all Intermediate tier challenges", "criteria_type": "tier_complete", "criteria_value": 12},
    {"name": "Advanced Graduate", "description": "Complete all Advanced tier challenges", "criteria_type": "tier_complete", "criteria_value": 11},
    {"name": "Quest Master", "description": "Complete every challenge in the game", "criteria_type": "all_challenges_complete", "criteria_value": 41},
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
            title, desc, method, path, headers, query, body, points, clues, hints, sandbox, time_limit = c
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
                existing.clues = clues
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
                    clues=clues,
                    hints=hints,
                    order_index=idx + 1,
                    sandbox_endpoint=sandbox,
                    time_limit_seconds=time_limit,
                )
                db.add(challenge)
                created_challenges += 1

    # ── Prune removed challenges ─────────────────────────────────
    all_seed_titles = set()
    for track_title, challenges in CHALLENGES.items():
        for c in challenges:
            all_seed_titles.add((track_title, c[0]))  # (track_title, challenge_title)

    removed_challenges = 0
    for track_title, track in track_objects.items():
        db_challenges = db.query(Challenge).filter_by(track_id=track.id).all()
        for ch in db_challenges:
            if (track_title, ch.title) not in all_seed_titles:
                db.delete(ch)
                removed_challenges += 1

    # Reconcile all UserTrackProgress rows (handles count drift from
    # added/removed challenges or any prior bugs)
    from app.models.gamification import UserTrackProgress
    from app.services.gamification_service import check_and_award_badges, update_track_progress
    all_progress_rows = db.query(UserTrackProgress).all()
    reconciled_user_ids = set()
    for row in all_progress_rows:
        update_track_progress(db, row.user_id, row.track_id)
        reconciled_user_ids.add(row.user_id)
    for uid in reconciled_user_ids:
        check_and_award_badges(db, uid)

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
    parts = []
    if total_new:
        parts.append(f"created {created_tracks}t/{created_challenges}c/{created_badges}b")
    if total_upd:
        parts.append(f"updated {updated_tracks}t/{updated_challenges}c/{updated_badges}b")
    if removed_challenges:
        parts.append(f"removed {removed_challenges} stale challenges")
    if parts:
        print(f"Seed: {', '.join(parts)}.")
    else:
        print(f"Seed data up-to-date ({updated_tracks} tracks, {updated_challenges} challenges, {updated_badges} badges).")


if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_database(db)
