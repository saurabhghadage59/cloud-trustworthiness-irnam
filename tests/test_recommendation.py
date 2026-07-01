import unittest

from negotiation.utils import provider_name_from_recommendation
from src.recommendation.models import Requirement, RequirementAttribute, RequirementPriority
from src.recommendation.ranking import ProviderRanker
from src.recommendation.recommendation_engine import RecommendationEngine
from src.recommendation.user_input import UserRequirementProcessor
from src.recommendation.weights import WeightCalculator


def requirement(**priorities):
    attributes = {
        name: RequirementAttribute(name, RequirementPriority.from_value(priority), priority)
        for name, priority in priorities.items()
    }
    return Requirement(attributes, list(attributes), {name: item.priority.value for name, item in attributes.items()})


class WeightCalculatorTests(unittest.TestCase):
    def test_weights_are_normalized_and_follow_priority(self):
        weights = WeightCalculator().calculate_user_weights({"latency": "very_high", "price": "low", "memory": "medium"})
        self.assertAlmostEqual(1.0, sum(weights.values()))
        self.assertGreater(weights["latency"], weights["memory"])
        self.assertGreater(weights["memory"], weights["price"])

    def test_any_attribute_names_are_supported(self):
        weights = WeightCalculator().calculate_user_weights({"custom_a": 3, "custom_b": 1})
        self.assertEqual({"custom_a", "custom_b"}, set(weights))

    def test_provider_weights_derive_from_typed_values(self):
        providers = [{"provider_name": "A", "quality": 10}, {"provider_name": "B", "quality": 30}]
        weights = WeightCalculator().calculate_provider_weights(providers, ["quality"])
        self.assertAlmostEqual(1.0, weights["A"]["quality"] + weights["B"]["quality"])
        self.assertGreater(weights["B"]["quality"], weights["A"]["quality"])


class RankingTests(unittest.TestCase):
    def test_benefit_and_cost_attributes_are_ranked(self):
        providers = [
            {"provider_name": "A", "quality": 80, "price": 5},
            {"provider_name": "B", "quality": 100, "price": 10},
        ]
        ranking = ProviderRanker().rank_providers(
            providers,
            {"quality": 0.8, "price": 0.2},
            directions={"price": "lower"},
        )
        self.assertEqual("B", ranking[0].provider)
        self.assertEqual(1, ranking[0].rank)
        self.assertGreater(ranking[0].overall_score, ranking[1].overall_score)

    def test_ties_receive_same_dense_rank(self):
        providers = [{"provider_name": "A", "quality": 10}, {"provider_name": "B", "quality": 10}]
        ranking = ProviderRanker().rank_providers(providers, {"quality": 1.0})
        self.assertEqual([1, 1], [entry.rank for entry in ranking])

    def test_missing_values_score_zero(self):
        providers = [{"provider_name": "A", "quality": None}, {"provider_name": "B", "quality": 10}]
        ranking = ProviderRanker().rank_providers(providers, {"quality": 1.0})
        self.assertEqual("B", ranking[0].provider)
        self.assertEqual(0.0, ranking[1].attribute_scores["quality"])


class RecommendationEngineTests(unittest.TestCase):
    def setUp(self):
        self.providers = [
            {"provider_name": "Alpha", "quality": 80, "price": 4, "kubernetes": True},
            {"provider_name": "Beta", "quality": 100, "price": 8, "kubernetes": True},
            {"provider_name": "Gamma", "quality": 90, "price": 6, "kubernetes": False},
        ]
        self.engine = RecommendationEngine(
            providers=self.providers,
            attribute_mapping={"quality": "quality", "price": "price"},
            directions={"price": "lower"},
        )
        self.requirement = requirement(quality="very_high", price="low")

    def test_recommendation_returns_complete_result(self):
        result = self.engine.recommend(self.requirement)
        self.assertEqual("Beta", result.recommended_provider)
        self.assertEqual(3, len(result.complete_ranking))
        self.assertTrue(result.attribute_scores)
        self.assertIn("best overall evaluation score", result.reason_for_recommendation)

    def test_filtering_handles_services_constraints_and_unavailable_providers(self):
        result = self.engine.recommend(
            self.requirement,
            constraints={"quality": {"min": 85}},
            requested_services=["kubernetes"],
            unavailable_providers=["Beta"],
        )
        self.assertIsNone(result.recommended_provider)
        self.assertEqual({"Alpha", "Beta", "Gamma"}, set(result.filtered_out))

    def test_mandatory_requirement_filters_provider(self):
        result = self.engine.recommend(self.requirement, mandatory_requirements={"kubernetes": True})
        self.assertNotIn("Gamma", [entry.provider for entry in result.complete_ranking])

    def test_result_is_directly_consumable_by_negotiation(self):
        result = self.engine.recommend(self.requirement)
        self.assertEqual("Beta", provider_name_from_recommendation(result))
        self.assertEqual("Beta", dict(result)["recommended_provider"])

    def test_real_structured_dataset_pipeline_executes(self):
        parsed = UserRequirementProcessor().process({
            "availability": "very_high", "reliability": "high", "security": "high",
            "cost": "medium", "response_time": "low", "scalability": "high",
            "support": "medium", "storage": "low", "network": "medium",
        })
        result = RecommendationEngine().recommend(parsed)
        self.assertIsNotNone(result.recommended_provider)
        self.assertEqual(5, len(result.complete_ranking))


if __name__ == "__main__":
    unittest.main()
