import unittest

from evaluation.negotiation_metrics import calculate_negotiation_metrics
from negotiation.aggregation import AggregationEngine
from negotiation.concession import calculate_concession
from negotiation.models import AttributeSpec, NegotiationConfig, Offer
from negotiation.negotiation import NegotiationAgent
from negotiation.negotiation_engine import NegotiationEngine
from sla.sla_manager import SLAManager
from sla.sla_parser import SLAParser
from sla.sla_validator import SLAValidator


class ConcessionTests(unittest.TestCase):
    def test_legacy_midpoint_concession_is_preserved(self):
        self.assertEqual(calculate_concession(100, 200), 150)

    def test_strategy_rho_changes_concession(self):
        kwargs = {
            "negotiation_time": 0.75,
            "degree_of_difference": 0.48,
            "user_aggregate": 0.0732,
        }
        competitive = calculate_concession(strategy="competitive", **kwargs)
        win_win = calculate_concession(strategy="win_win", **kwargs)
        collaborative = calculate_concession(strategy="collaborative", **kwargs)

        self.assertGreater(competitive, win_win)
        self.assertGreater(win_win, collaborative)


class NegotiationEngineTests(unittest.TestCase):
    def setUp(self):
        self.recommendation = {
            "recommended_provider": "CSP1",
            "overall_score": 0.21,
            "user_priorities": {
                "price": 0.46,
                "security": 0.26,
                "response_time": 0.15,
                "availability": 0.09,
                "reliability": 0.04,
            },
        }
        self.user_sla = {
            "price": {"value": 100, "min": 95, "max": 120},
            "security": {"value": 90, "min": 85, "max": 95},
            "response_time": {"value": 15, "min": 10, "max": 20},
            "availability": {"value": 95, "min": 95, "max": 100},
            "reliability": {"value": 98, "min": 95, "max": 100},
        }
        self.provider_sla = {
            "price": {"value": 125, "min": 105, "max": 130},
            "security": {"value": 75, "min": 70, "max": 80},
            "response_time": {"value": 25, "min": 20, "max": 30},
            "availability": {"value": 93, "min": 90, "max": 95},
            "reliability": {"value": 98, "min": 95, "max": 100},
            "weights": {
                "price": 0.46,
                "security": 0.04,
                "response_time": 0.09,
                "availability": 0.15,
                "reliability": 0.26,
            },
        }

    def test_negotiation_accepts_recommendation_output(self):
        engine = NegotiationEngine(
            NegotiationConfig(strategy="win_win", max_rounds=5, acceptance_threshold=0.0)
        )
        result = engine.negotiate(self.recommendation, self.user_sla, self.provider_sla)

        self.assertTrue(result.success)
        self.assertEqual(result.provider, "CSP1")
        self.assertIn("price", result.final_offer.attributes)
        self.assertGreaterEqual(
            result.satisfaction.user_satisfaction,
            result.satisfaction.provider_satisfaction,
        )

    def test_deadline_failure_requests_next_provider(self):
        engine = NegotiationEngine(
            NegotiationConfig(max_rounds=5, deadline_seconds=0, acceptance_threshold=0.0)
        )
        result = engine.negotiate(self.recommendation, self.user_sla, self.provider_sla)

        self.assertFalse(result.success)
        self.assertTrue(result.deadline_reached)
        self.assertIn("next provider", result.reason)

    def test_legacy_agent_still_returns_attribute_dictionary(self):
        agent = NegotiationAgent(
            {"price": 200, "security": 90, "availability": 95},
            {"price": 300, "security": 80, "availability": 92},
            config=NegotiationConfig(acceptance_threshold=0.0),
        )
        result = agent.negotiate()

        self.assertIsInstance(result, dict)
        self.assertIn("price", result)


class AggregationTests(unittest.TestCase):
    def test_rejects_when_user_satisfaction_is_below_provider(self):
        specs = [
            AttributeSpec(
                name="security",
                user_value=90,
                provider_value=75,
                user_weight=0.1,
                provider_weight=1.0,
                user_min=70,
                user_max=100,
                provider_min=70,
                provider_max=100,
            )
        ]
        offer = Offer(provider="CSP1", attributes={"security": 75})

        result = AggregationEngine().aggregate(offer, specs)

        self.assertFalse(result.accepted)


class SLATests(unittest.TestCase):
    def test_contract_serialization_validation_and_comparison(self):
        engine = NegotiationEngine(NegotiationConfig(acceptance_threshold=0.0))
        negotiation = engine.negotiate(
            {"recommended_provider": "CSP1", "user_priorities": {"price": 1}},
            {"price": {"value": 100, "min": 90, "max": 120}},
            {"price": {"value": 110, "min": 90, "max": 120}},
        )
        contract = SLAManager().create_contract(negotiation)
        payload = contract.to_json()
        parsed = SLAParser().parse(payload)
        validation = SLAValidator().validate_contract(contract)

        self.assertTrue(validation.valid)
        self.assertEqual(parsed["provider"], "CSP1")
        self.assertEqual(contract.compare(contract)["changed_attributes"], {})


class EvaluationTests(unittest.TestCase):
    def test_metrics_summarize_negotiation_results(self):
        engine = NegotiationEngine(NegotiationConfig(acceptance_threshold=0.0))
        result = engine.negotiate(
            {"recommended_provider": "CSP1", "user_priorities": {"price": 1}},
            {"price": {"value": 100, "min": 90, "max": 120}},
            {"price": {"value": 110, "min": 90, "max": 120}},
        )

        metrics = calculate_negotiation_metrics([result])

        self.assertEqual(metrics.total_runs, 1)
        self.assertEqual(metrics.negotiation_success_rate, 1.0)
        self.assertGreaterEqual(metrics.average_negotiation_rounds, 1)


if __name__ == "__main__":
    unittest.main()
