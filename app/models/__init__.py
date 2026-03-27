# Import all models so SQLAlchemy relationships resolve correctly
from app.models.challenge import Challenge, Track  # noqa: F401
from app.models.gamification import Badge, HintReveal, UserBadge, UserTrackProgress  # noqa: F401
from app.models.submission import Submission  # noqa: F401
from app.models.user import User  # noqa: F401
