import unittest

from src.recommendation.models import RequirementPriority
from src.recommendation.user_input import UserRequirementProcessor
from src.recommendation.validation import RequirementValidationError


class UserRequirementProcessingTests(unittest.TestCase):
    def setUp(self):
        self.processor = UserRequirementProcessor()

    def test_process_builds_structured_requirement(self):
        request = {
            "availability": "Very High",
            "security": "High",
            "cost": "Medium",
            "reliability": "High",
            "response_time": "Low",
            "scalability": "Medium",
            "support": "Medium",
            "storage": "Low",
            "network": "Medium",
        }

        requirement = self.processor.process(request)

        self.assertEqual(requirement.attributes["availability"].priority, RequirementPriority.VERY_HIGH)
        self.assertEqual(requirement.attributes["cost"].priority, RequirementPriority.MEDIUM)
        self.assertEqual(requirement.attributes["security"].priority, RequirementPriority.HIGH)
        self.assertEqual(requirement.attribute_names, [
            "availability",
            "reliability",
            "security",
            "cost",
            "response_time",
            "scalability",
            "support",
            "storage",
            "network",
        ])
        self.assertEqual(requirement.priority_values["availability"], "very_high")

    def test_missing_attributes_raise_meaningful_error(self):
        request = {
            "availability": "High",
            "security": "High",
            "cost": "Medium",
        }

        with self.assertRaises(RequirementValidationError) as context:
            self.processor.process(request)

        self.assertIn("Missing required attributes", str(context.exception))
        self.assertIn("reliability", str(context.exception))

    def test_duplicate_priorities_raise_error(self):
        request = [
            ("availability", "High"),
            ("reliability", "High"),
            ("security", "Medium"),
            ("cost", "Low"),
            ("response_time", "Low"),
            ("scalability", "Low"),
            ("support", "Low"),
            ("storage", "Low"),
            ("network", "Low"),
            ("availability", "Very High"),
        ]

        with self.assertRaises(RequirementValidationError) as context:
            self.processor.process(request)

        self.assertIn("Duplicate priorities", str(context.exception))

    def test_invalid_priority_value_is_rejected(self):
        request = {
            "availability": "Extremely High",
            "reliability": "High",
            "security": "Medium",
            "cost": "Low",
            "response_time": "Low",
            "scalability": "Low",
            "support": "Low",
            "storage": "Low",
            "network": "Low",
        }

        with self.assertRaises(RequirementValidationError) as context:
            self.processor.process(request)

        self.assertIn("Invalid priority value", str(context.exception))

    def test_empty_request_is_rejected(self):
        with self.assertRaises(RequirementValidationError) as context:
            self.processor.process({})

        self.assertIn("Empty request", str(context.exception))


if __name__ == "__main__":
    unittest.main()
