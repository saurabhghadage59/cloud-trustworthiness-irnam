import unittest
from pathlib import Path

from negotiation.utils import provider_name_from_recommendation
from src.recommendation.models import Requirement, RequirementAttribute, RequirementPriority
from src.recommendation.m_topsis import MultiLayeredTOPSISStrategy
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


class MultiLayeredTOPSISTests(unittest.TestCase):
    def test_category_ranking_uses_category_local_topsis_score(self):
        providers = [
            {"provider_name": "A", "throughput": 100, "latency": 10},
            {"provider_name": "B", "throughput": 50, "latency": 20},
            {"provider_name": "C", "throughput": 10, "latency": 40},
        ]
        strategy = MultiLayeredTOPSISStrategy(
            category_mapping={"performance": ("throughput", "latency")},
            category_weights={"performance": 1.0},
        ).fit(providers, {"throughput": 0.7, "latency": 0.3}, {"latency": "lower"})

        ranking = strategy.rank_category("performance")
        self.assertEqual("A", ranking[0].provider)
        self.assertGreater(ranking[0].overall_score, ranking[-1].overall_score)

    def test_cost_criteria_make_lower_values_closer_to_ideal(self):
        providers = [
            {"provider_name": "Cheap", "cost": 1.0},
            {"provider_name": "Expensive", "cost": 5.0},
        ]
        ranking = MultiLayeredTOPSISStrategy(
            category_mapping={"economic": ("cost",)},
            category_weights={"economic": 1.0},
        ).fit(providers, {"cost": 1.0}, {"cost": "lower"}).rank()

        self.assertEqual("Cheap", ranking[0].provider)
        self.assertGreater(ranking[0].overall_score, ranking[1].overall_score)

    def test_configured_category_weights_are_normalized_and_change_winner(self):
        providers = [
            {"provider_name": "Fast", "throughput": 100, "cost": 10},
            {"provider_name": "Cheap", "throughput": 50, "cost": 1},
        ]
        category_mapping = {"performance": ("throughput",), "economic": ("cost",)}

        performance_first = MultiLayeredTOPSISStrategy(
            category_mapping=category_mapping,
            category_weights={"performance": 8, "economic": 2},
        ).fit(providers, {"throughput": 0.5, "cost": 0.5}, {"cost": "lower"})
        economic_first = MultiLayeredTOPSISStrategy(
            category_mapping=category_mapping,
            category_weights={"performance": 2, "economic": 8},
        ).fit(providers, {"throughput": 0.5, "cost": 0.5}, {"cost": "lower"})

        self.assertAlmostEqual(1.0, sum(performance_first.category_weights.values()))
        self.assertEqual("Fast", performance_first.rank()[0].provider)
        self.assertEqual("Cheap", economic_first.rank()[0].provider)


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

    def test_m_topsis_integration_returns_negotiation_ready_result(self):
        engine = RecommendationEngine(
            providers=self.providers,
            attribute_mapping={"quality": "quality", "price": "price"},
            directions={"price": "lower"},
            algorithm="mtopsis",
            category_mapping={"performance": ("quality",), "economic": ("price",)},
            category_weights={"performance": 8, "economic": 2},
        )
        result = engine.recommend(self.requirement)

        self.assertEqual("Beta", result.recommended_provider)
        self.assertEqual("Beta", provider_name_from_recommendation(result))
        self.assertTrue(all(isinstance(entry.provider_attributes, dict) for entry in result.complete_ranking))

    def test_m_topsis_hyphen_alias_is_supported(self):
        engine = RecommendationEngine(
            providers=self.providers,
            attribute_mapping={"quality": "quality", "price": "price"},
            directions={"price": "lower"},
            algorithm="m-topsis",
            category_mapping={"performance": ("quality",), "economic": ("price",)},
            category_weights={"performance": 8, "economic": 2},
        )
        self.assertEqual("Beta", engine.recommend(self.requirement).recommended_provider)

    def test_irnam_weighted_baseline_regression_is_preserved(self):
        engine = RecommendationEngine(
            providers=self.providers,
            attribute_mapping={"quality": "quality", "price": "price"},
            directions={"price": "lower"},
            algorithm="IRNAM_Weighted",
        )
        result = engine.recommend(self.requirement)

        self.assertEqual("Beta", result.recommended_provider)
        self.assertAlmostEqual(0.714285714286, result.overall_score)

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

    def test_mentor_qos_schema_is_adapted_without_legacy_columns(self):
        """Service-name QoS CSVs remain rankable when optional IRNAM fields are absent."""
        dataset = Path(__file__).resolve().parents[1] / "src" / "dataset" / "cloud_dataset.csv"
        engine = RecommendationEngine(dataset_path=dataset)
        rows = engine.load_dataset()
        self.assertEqual("MAPPMatching", rows[0]["provider_name"])
        self.assertTrue({"availability", "reliability", "throughput", "response_time", "latency", "documentation", "best_practices"}.issubset(rows[0]))
        result = engine.recommend(requirement(
            availability="very_high", reliability="high", throughput="high", response_time="low",
            latency="low", documentation="medium", best_practices="high",
        ))
        self.assertIsNotNone(result.recommended_provider)
        self.assertEqual({"availability", "reliability", "throughput", "response_time", "latency", "documentation", "best_practices"}, set(result.user_weights))
        self.assertEqual(len(result.complete_ranking), len({row.provider for row in result.complete_ranking}))


if __name__ == "__main__":
    unittest.main()
