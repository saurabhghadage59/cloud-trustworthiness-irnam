"""Public API for the IRNAM recommendation phase."""

from .models import Requirement, RequirementAttribute, RequirementPriority
from .ranking import ProviderRanker, RankedProvider, RankingEngine
from .recommendation_engine import RecommendationEngine, RecommendationResult
from .user_input import UserRequirementProcessor
from .weights import WeightCalculator
from .normalization import Normalizer, normalize
from .algorithms import RecommendationStrategy, create_strategy
from .m_topsis import MultiLayeredTOPSISStrategy

__all__ = [
    "ProviderRanker",
    "RankedProvider",
    "RankingEngine",
    "RecommendationEngine",
    "RecommendationResult",
    "Requirement",
    "RequirementAttribute",
    "RequirementPriority",
    "UserRequirementProcessor",
    "WeightCalculator",
    "Normalizer",
    "normalize",
    "RecommendationStrategy",
    "create_strategy",
    "MultiLayeredTOPSISStrategy",
]
