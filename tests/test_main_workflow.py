import unittest
from pathlib import Path

from main import run_workflow
from negotiation import NegotiationConfig


class MainWorkflowTests(unittest.TestCase):
    def test_default_demo_runs_every_phase(self):
        result = run_workflow(
            Path("outputs/cloud_dataset.json"),
            negotiation_config=NegotiationConfig(
                strategy="win_win",
                max_rounds=10,
                acceptance_threshold=0.0,
            ),
        )

        self.assertEqual(5, result.provider_count)
        self.assertIsNotNone(result.recommendation.recommended_provider)
        self.assertTrue(result.negotiation.success)
        self.assertEqual("accepted", result.sla_contract.agreement_status)
        self.assertEqual(1, result.evaluation.total_runs)
        self.assertEqual(1.0, result.evaluation.negotiation_success_rate)


if __name__ == "__main__":
    unittest.main()
