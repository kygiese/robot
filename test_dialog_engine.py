"""
Tests for DialogEngine — validates all features required by the
CSCI 455 Project 2 test script (testDialogFileForPractice.txt).
"""

import unittest
from services.DialogEngine import DialogEngine


class TestDialogEngineWithTestScript(unittest.TestCase):
    """Integration tests using the full test script."""

    @classmethod
    def setUpClass(cls):
        cls.engine = DialogEngine()
        cls.loaded = cls.engine.load_script("testDialogFileForPractice.txt")

    def setUp(self):
        self.engine.reset()

    # ---- Loading and error reporting ------------------------------------

    def test_script_loads_successfully(self):
        self.assertTrue(self.loaded)

    def test_deliberate_errors_detected(self):
        categories = [e.category for e in self.engine.errors]
        # Line 117: missing second colon
        self.assertIn("UNRECOGNIZED_LINE", categories)
        # Line 120: unbalanced bracket in output
        self.assertIn("UNBALANCED_BRACKET", categories)
        # Line 137-138: max depth exceeded
        self.assertIn("MAX_DEPTH", categories)

    def test_unbalanced_bracket_rule_not_loaded(self):
        for rule in self.engine.rules:
            self.assertNotIn("bad bracket", rule.pattern_str)

    # ---- Definitions ----------------------------------------------------

    def test_definitions_loaded(self):
        for name in ("greet", "bye", "affirm", "deny", "thanks",
                     "dance_words", "arm_words", "whoami", "howold"):
            self.assertIn(name, self.engine.definitions)

    # ---- Greeting + output choices + action tag -------------------------

    def test_greeting_matches(self):
        resp, actions = self.engine.process_input("hello")
        self.assertIn(resp, ["hi", "hello", "what up", "sup"])
        self.assertEqual(actions, ["arm_raise"])

    def test_greeting_all_definition_forms(self):
        for word in ("hi", "howdy", "hi there", "hey robot"):
            self.engine.reset()
            resp, actions = self.engine.process_input(word)
            self.assertIsNotNone(resp, f"No match for greeting '{word}'")
            self.assertIn("arm_raise", actions)

    # ---- Scoped u1 rules after greeting ---------------------------------

    def test_u1_affirm_after_greeting(self):
        self.engine.process_input("hello")
        resp, actions = self.engine.process_input("yes")
        self.assertEqual(resp, "Great!")
        self.assertEqual(actions, ["head_yes"])

    def test_u1_deny_after_greeting(self):
        self.engine.process_input("hello")
        resp, actions = self.engine.process_input("no")
        self.assertEqual(resp, "No worries.")
        self.assertEqual(actions, ["head_no"])

    def test_u1_quoted_phrase_pattern(self):
        self.engine.process_input("hello")
        resp, actions = self.engine.process_input("hi there")
        self.assertEqual(resp, "Hey, you said the special greeting.")
        self.assertEqual(actions, ["arm_raise"])

    def test_u1_multiple_actions(self):
        self.engine.process_input("hello")
        resp, actions = self.engine.process_input("you are awesome")
        self.assertEqual(resp, "Thanks!")
        self.assertEqual(actions, ["head_yes", "arm_raise"])

    def test_u1_whitespace_tolerance(self):
        self.engine.process_input("hello")
        resp, actions = self.engine.process_input("and")
        self.assertEqual(resp, "and-and-and!")
        self.assertEqual(actions, ["head_yes"])

    # ---- Variable capture and recall ------------------------------------

    def test_variable_capture(self):
        resp, actions = self.engine.process_input("my name is Alice")
        self.assertIn("alice", resp.lower())
        self.assertEqual(actions, ["head_yes"])

    def test_variable_recall(self):
        self.engine.process_input("my name is Alice")
        resp, _ = self.engine.process_input("what is my name")
        self.assertIn("alice", resp.lower())

    def test_unset_variable_placeholder(self):
        resp, _ = self.engine.process_input("what is my favorite color")
        self.assertIn("I don't know", resp)

    # ---- Stop / safety command ------------------------------------------

    def test_stop_command(self):
        resp, _ = self.engine.process_input("stop")
        self.assertEqual(resp, "OK. Stopping now.")

    # ---- Nested scopes (u -> u1 -> u2) ----------------------------------

    def test_nested_scopes(self):
        resp, _ = self.engine.process_input("let us talk")
        self.assertEqual(resp, "Sure. Ask me a question.")

        resp, actions = self.engine.process_input("are you sad")
        self.assertIn(resp, ["no", "not today"])
        self.assertEqual(actions, ["head_no"])

        resp, actions = self.engine.process_input("why")
        self.assertEqual(resp, "Because I am a robot.")
        self.assertEqual(actions, ["arm_raise"])

    # ---- Max depth guard ------------------------------------------------

    def test_max_depth_blocks_u6_and_deeper(self):
        self.engine.process_input("deep test")
        for expected in ("depth 2", "depth 3", "depth 4", "depth 5", "depth 6"):
            resp, _ = self.engine.process_input("go deeper")
            self.assertEqual(resp, expected)
        # depth 7 should NOT activate — no matching subrule
        resp, _ = self.engine.process_input("go deeper")
        self.assertIsNone(resp, "u6 rule should have been blocked")

    # ---- Definition in output -------------------------------------------

    def test_definition_expansion_in_output(self):
        resp, actions = self.engine.process_input("say hello")
        greet_opts = self.engine.definitions["greet"]
        self.assertIn(resp, greet_opts)
        self.assertEqual(actions, ["arm_raise"])

    # ---- Bracket choices with quoted phrases in pattern ------------------

    def test_bracket_pattern_with_quoted_phrase(self):
        for word in ("robot", "cool robot", "friend"):
            self.engine.reset()
            resp, actions = self.engine.process_input(word)
            self.assertEqual(resp, "I heard you.")
            self.assertEqual(actions, ["head_yes"])

    # ---- Unknown action tag ---------------------------------------------

    def test_unknown_action_extracted(self):
        resp, actions = self.engine.process_input("do the secret move")
        self.assertEqual(resp, "Absolutely.")
        self.assertEqual(actions, ["moonwalk"])

    # ---- Thanks and goodbye ---------------------------------------------

    def test_thanks(self):
        resp, actions = self.engine.process_input("thanks")
        self.assertEqual(resp, "You are welcome.")
        self.assertEqual(actions, ["head_yes"])

    def test_goodbye(self):
        resp, actions = self.engine.process_input("goodbye")
        self.assertEqual(resp, "Goodbye!")
        self.assertEqual(actions, ["arm_raise"])


class TestActionRunnerWarning(unittest.TestCase):
    """Test that unknown actions produce a warning."""

    def test_unknown_action_warns(self):
        from unittest.mock import MagicMock
        from io import StringIO
        import sys

        from ActionRunner import ActionRunner

        mock_robot = MagicMock()
        runner = ActionRunner(mock_robot)

        captured = StringIO()
        sys.stdout = captured
        try:
            runner.run_action("moonwalk")
        finally:
            sys.stdout = sys.__stdout__

        self.assertIn("unknown action", captured.getvalue().lower())


if __name__ == "__main__":
    unittest.main()
