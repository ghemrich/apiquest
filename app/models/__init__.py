# Import all models so SQLAlchemy relationships resolve correctly
from app.models.user import User  # noqa: F401
from app.models.challenge import Track, Challenge  # noqa: F401
from app.models.submission import Submission  # noqa: F401
from app.models.gamification import Badge, UserBadge, UserTrackProgress, HintReveal  # noqa: F401
