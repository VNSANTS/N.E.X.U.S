"""N.E.X.U.S. lightweight learning core."""

from .engine import LearningEngine
from .cognitive import CognitiveAdaptation
from .permissions import PermissionManager

__all__ = ["LearningEngine", "CognitiveAdaptation", "PermissionManager"]
