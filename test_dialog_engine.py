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

    # ---- Global interrupt -----------------------------------------------

    def test_global_interrupt_from_scope(self):
        """Interrupt word while in a u1 scope should match the top-level
        stop rule, clear scope, and set the interrupted flag."""
        self.engine.process_input("hello")              # enter scope
        self.assertTrue(len(self.engine.active_subrules) > 0)

        resp, _ = self.engine.process_input("stop")
        self.assertEqual(resp, "OK. Stopping now.")
        self.assertTrue(self.engine.was_interrupted())
        self.assertEqual(self.engine.active_subrules, [])

    def test_global_interrupt_all_keywords(self):
        """All four interrupt words should work, case-insensitive."""
        for word in ("Stop", "CANCEL", "Reset", "QUIT"):
            self.engine.reset()
            self.engine.process_input("hello")          # enter scope
            resp, _ = self.engine.process_input(word)
            self.assertEqual(resp, "OK. Stopping now.",
                             f"Interrupt word '{word}' failed")
            self.assertTrue(self.engine.was_interrupted())
            self.assertEqual(self.engine.active_subrules, [])

    def test_no_interrupt_flag_on_normal_input(self):
        """Regular input should NOT set the interrupted flag."""
        resp, _ = self.engine.process_input("hello")
        self.assertFalse(self.engine.was_interrupted())

    def test_interrupt_clears_variables(self):
        """Global interrupt should also clear captured variables."""
        self.engine.process_input("my name is Alice")
        self.assertIn("name", self.engine.variables)

        self.engine.process_input("quit")
        self.assertEqual(self.engine.variables, {})

    # ---- Unknown input scope exit ---------------------------------------

    def test_scope_exit_after_four_unknowns(self):
        """Four consecutive unrecognized inputs in a scope should exit
        the scope so the engine returns to IDLE."""
        self.engine.process_input("hello")              # enter scope
        self.assertTrue(len(self.engine.active_subrules) > 0)

        for _ in range(4):
            resp, _ = self.engine.process_input("xyzzy gibberish")
            self.assertIsNone(resp)

        # Scope should now be cleared
        self.assertEqual(self.engine.active_subrules, [])

    def test_scope_stays_if_fewer_than_four_unknowns(self):
        """Fewer than four unknowns should NOT exit the scope."""
        self.engine.process_input("hello")              # enter scope
        for _ in range(3):
            self.engine.process_input("xyzzy gibberish")
        self.assertTrue(len(self.engine.active_subrules) > 0)

    def test_unknown_counter_resets_on_match(self):
        """A successful match resets the unknown counter."""
        # Enter the 'let us talk' scope which has u1 rules
        self.engine.process_input("let us talk")
        self.engine.process_input("xyzzy gibberish")    # unknown 1
        self.engine.process_input("xyzzy gibberish")    # unknown 2
        # Match u1:(are you sad) — resets counter, activates u2 scope
        resp, _ = self.engine.process_input("are you sad")
        self.assertIsNotNone(resp)
        self.assertEqual(self.engine._unknown_count, 0)
        # 3 more unknowns should NOT exit (only 3, need 4)
        for _ in range(3):
            self.engine.process_input("xyzzy gibberish")
        self.assertEqual(self.engine._unknown_count, 3)

    def test_unknown_counter_not_active_outside_scope(self):
        """Unknown inputs at the top level should not trigger scope exit."""
        for _ in range(5):
            resp, _ = self.engine.process_input("xyzzy gibberish")
            self.assertIsNone(resp)
        # No scope was active, so nothing should have changed
        self.assertEqual(self.engine.active_subrules, [])


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


class TestActionRunnerCancellation(unittest.TestCase):
    """Test that ActionRunner cancellation stops action sequences."""

    def test_cancel_stops_remaining_actions(self):
        from unittest.mock import MagicMock
        from ActionRunner import ActionRunner

        mock_robot = MagicMock()
        runner = ActionRunner(mock_robot)

        # Cancel then call run_action directly — should be a no-op
        runner.cancel()
        runner.run_action("head_yes")

        # head_tilt should not have been called
        mock_robot.head_tilt.assert_not_called()

    def test_run_actions_clears_cancel(self):
        from unittest.mock import MagicMock
        from ActionRunner import ActionRunner

        mock_robot = MagicMock()
        runner = ActionRunner(mock_robot)

        # Cancel, then start a new sequence — cancel should be cleared
        runner.cancel()
        runner.run_actions(["head_yes"])
        mock_robot.head_tilt.assert_called()


if __name__ == "__main__":
    unittest.main()
