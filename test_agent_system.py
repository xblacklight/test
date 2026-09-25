import unittest
from agent_system import Orchestrator, ReceiverAgent, Thought, DeliveryAgent


class PipelineTests(unittest.TestCase):
    def test_receiver_normalizes_and_extracts_constraints(self):
        brief = ReceiverAgent().receive("Build an API. It must return JSON.")
        self.assertEqual(brief.original_request, "Build an API. It must return JSON.")
        self.assertEqual(len(brief.requirements), 2)
        self.assertIn("It must return JSON.", brief.constraints)

    def test_pipeline_delivers_only_after_qc(self):
        package = Orchestrator().run("Create a small command line tool.")
        self.assertEqual(package.status, "ready")
        self.assertTrue(package.verification["passed"])
        self.assertTrue(package.artifact)

    def test_delivery_rejects_empty_thought(self):
        brief = ReceiverAgent().receive("Do something")
        thought = Thought("", [], [], "")
        package = DeliveryAgent().deliver(brief, thought)
        self.assertEqual(package.status, "rejected")
        self.assertFalse(package.verification["passed"])

    def test_empty_request_is_rejected(self):
        with self.assertRaises(ValueError):
            Orchestrator().run("  ")


if __name__ == "__main__":
    unittest.main()
