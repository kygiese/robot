"""
Basic tests for the dialog engine (dialog_engine.py).

Run with: python -m pytest test_dialog.py -v
"""

import os
import sys
import tempfile
import pytest

# Add repo root to path
sys.path.insert(0, os.path.dirname(__file__))
from dialog_engine import DialogEngine, EngineState, ParseError


# ========== Helpers ==========

def make_engine(script_content: str) -> DialogEngine:
    """Write a temp script and load it into a fresh engine."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(script_content)
        fname = f.name
    engine = DialogEngine(filename=fname)
    os.unlink(fname)
    return engine


# ========== Script Parsing Tests ==========

class TestParsing:
    def test_basic_rule_loads(self):
        engine = make_engine("u:(hello): hi there\n")
        assert engine.is_loaded
        assert len(engine.top_rules) == 1

    def test_blank_lines_ignored(self):
        engine = make_engine("\n\nu:(hello): hi\n\n")
        assert engine.is_loaded

    def test_comment_ignored(self):
        engine = make_engine("# this is a comment\nu:(hello): hi\n")
        assert engine.is_loaded
        assert len(engine.top_rules) == 1

    def test_inline_comment_stripped(self):
        engine = make_engine("u:(hello): hi # inline comment\n")
        # Rule should load without the comment
        result = engine.process_input("hello")
        assert "hi" in result["response"]
        assert "inline comment" not in result["response"]

    def test_definition_loaded(self):
        engine = make_engine("~greet: [hello hi hey]\nu:(~greet): hi\n")
        assert "greet" in engine.definitions
        assert "hello" in engine.definitions["greet"]

    def test_definition_with_quoted_phrase(self):
        engine = make_engine('~test: [one two "three four"]\nu:(~test): ok\n')
        assert "three four" in engine.definitions["test"]

    def test_fatal_error_no_rules(self):
        engine = make_engine("# nothing here\n")
        assert not engine.is_loaded
        fatal_errors = [e for e in engine.parse_errors if e.fatal]
        assert len(fatal_errors) > 0

    def test_non_fatal_syntax_error_continues(self):
        # Bad line + good line: should still load
        engine = make_engine("bad line no colon\nu:(hello): hi\n")
        assert engine.is_loaded  # continues past bad line
        assert len(engine.top_rules) >= 1

    def test_missing_colon_after_pattern(self):
        # Missing ':' after pattern - non-fatal
        engine = make_engine("u:(missing colon) no colon\nu:(hello): hi\n")
        assert engine.is_loaded
        assert len(engine.top_rules) >= 1

    def test_parse_error_has_filename_and_lineno(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("bad line\nu:(hello): hi\n")
            fname = f.name
        engine = DialogEngine(filename=fname)
        os.unlink(fname)
        non_fatal = [e for e in engine.parse_errors if not e.fatal]
        assert len(non_fatal) > 0
        assert non_fatal[0].filename == fname
        assert non_fatal[0].line_number > 0

    def test_hierarchical_rules(self):
        script = "u:(hello): hi\nu1:(how are you): fine\nu1:(bye): goodbye\n"
        engine = make_engine(script)
        assert len(engine.top_rules) == 1
        assert len(engine.top_rules[0].subrules) == 2

    def test_deep_nesting(self):
        script = (
            "u:(a): level0\n"
            "u1:(b): level1\n"
            "u2:(c): level2\n"
        )
        engine = make_engine(script)
        assert len(engine.top_rules) == 1
        assert len(engine.top_rules[0].subrules) == 1
        assert len(engine.top_rules[0].subrules[0].subrules) == 1


# ========== Pattern Matching Tests ==========

class TestMatching:
    def test_simple_literal_match(self):
        engine = make_engine("u:(hello): hi\n")
        result = engine.process_input("hello")
        assert result["matched"]
        assert result["response"] == "hi"

    def test_case_insensitive(self):
        engine = make_engine("u:(hello): hi\n")
        result = engine.process_input("HELLO")
        assert result["matched"]

    def test_punctuation_ignored(self):
        engine = make_engine("u:(hello): hi\n")
        result = engine.process_input("hello!")
        assert result["matched"]
        result2 = engine.process_input("hello.")
        assert result2["matched"]

    def test_bracket_choice_in_pattern(self):
        engine = make_engine("u:([hi hello hey]): matched\n")
        assert engine.process_input("hi")["matched"]
        assert engine.process_input("hello")["matched"]
        assert engine.process_input("hey")["matched"]
        assert not engine.process_input("bye")["matched"]

    def test_quoted_phrase_in_bracket(self):
        engine = make_engine('u:([hi "good morning"]): matched\n')
        assert engine.process_input("hi")["matched"]
        assert engine.process_input("good morning")["matched"]

    def test_definition_in_pattern(self):
        engine = make_engine("~greet: [hello hi]\nu:(~greet): matched\n")
        assert engine.process_input("hello")["matched"]
        assert engine.process_input("hi")["matched"]

    def test_no_match_returns_not_matched(self):
        engine = make_engine("u:(hello): hi\n")
        result = engine.process_input("goodbye")
        assert not result["matched"]

    def test_wildcard_capture(self):
        engine = make_engine("u:(my name is _): Hello $name.\n")
        result = engine.process_input("my name is Alice")
        assert result["matched"]
        assert "Alice" in result["response"]

    def test_named_capture(self):
        engine = make_engine("u:(i am _age years old): You are $age.\n")
        result = engine.process_input("i am 25 years old")
        assert result["matched"]
        assert "25" in result["response"]

    def test_variable_recall(self):
        engine = make_engine(
            "u:(my name is _): Hi $name.\n"
            "u:(what is my name): Your name is $name.\n"
        )
        engine.process_input("my name is Bob")
        result = engine.process_input("what is my name")
        assert "Bob" in result["response"]

    def test_unset_variable_returns_i_dont_know(self):
        engine = make_engine("u:(what is my color): $color\n")
        result = engine.process_input("what is my color")
        assert "I don't know" in result["response"]


# ========== Output Tests ==========

class TestOutput:
    def test_bracket_choice_output_is_one_of(self):
        engine = make_engine("u:(hello): [hi hello hey]\n")
        result = engine.process_input("hello")
        assert result["response"] in ["hi", "hello", "hey"]

    def test_definition_expanded_in_output(self):
        engine = make_engine("~greet: [hi hello]\nu:(say hi): ~greet\n")
        result = engine.process_input("say hi")
        assert result["response"] in ["hi", "hello"]

    def test_action_tags_extracted(self):
        engine = make_engine("u:(hello): hi <nod>\n")
        result = engine.process_input("hello")
        assert "<nod>" in result["action_tags"]
        assert "<nod>" not in result["response"]

    def test_multiple_action_tags(self):
        engine = make_engine("u:(great): yes <nod> <raise>\n")
        result = engine.process_input("great")
        assert "<nod>" in result["action_tags"]
        assert "<raise>" in result["action_tags"]
        assert "<nod>" not in result["response"]

    def test_unknown_action_tag_ignored_no_crash(self):
        engine = make_engine("u:(secret): ok <secret_move>\n")
        result = engine.process_input("secret")
        # Should not crash; tag appears in action_tags list
        assert result["matched"]


# ========== Scope / State Machine Tests ==========

class TestScope:
    def test_subrules_activated_after_top_rule_match(self):
        script = (
            "u:(hello): hi\n"
            "u1:(how are you): fine\n"
        )
        engine = make_engine(script)
        engine.process_input("hello")  # activate scope
        result = engine.process_input("how are you")
        assert result["matched"]
        assert result["response"] == "fine"

    def test_top_rule_match_clears_old_scope(self):
        script = (
            "u:(hello): hi\n"
            "u1:(how are you): fine\n"
            "u:(goodbye): bye\n"
        )
        engine = make_engine(script)
        engine.process_input("hello")   # enter scope with u1 subrules
        engine.process_input("goodbye")  # new top-level match clears scope
        # "how are you" should no longer match (scope was cleared)
        result = engine.process_input("how are you")
        assert not result["matched"]

    def test_scope_does_not_exceed_max_level(self):
        # Deep nesting: u6 should not activate subrules (MAX_SCOPE_LEVEL=6)
        script = (
            "u:(a): 0\n"
            "u1:(b): 1\n"
            "u2:(b): 2\n"
            "u3:(b): 3\n"
            "u4:(b): 4\n"
            "u5:(b): 5\n"
            "u6:(b): 6 SHOULD NOT ACTIVATE\n"
        )
        engine = make_engine(script)
        engine.process_input("a")
        for _ in range(5):
            engine.process_input("b")
        # At max level, u6 exists as subrule but engine should not activate it
        assert engine.active_level <= engine.MAX_SCOPE_LEVEL

    def test_state_is_running_after_load(self):
        engine = make_engine("u:(hello): hi\n")
        assert engine.state == EngineState.RUNNING

    def test_state_is_idle_before_load(self):
        engine = DialogEngine()
        assert engine.state == EngineState.IDLE


# ========== Safety Tests ==========

class TestSafety:
    def test_stop_word_triggers_interrupt(self):
        engine = make_engine("u:([stop cancel reset quit]): Stopping.\nu:(hello): hi\n")
        result = engine.process_input("stop")
        # Should clear scope and return a response
        assert result["matched"]

    def test_cancel_word_clears_scope(self):
        script = (
            "u:(hello): hi\n"
            "u1:(how are you): fine\n"
            "u:([stop cancel reset quit]): Stopping.\n"
        )
        engine = make_engine(script)
        engine.process_input("hello")
        engine.process_input("cancel")
        # Scope should be cleared
        assert engine.active_level == 0
        assert engine.active_subrules == []

    def test_reset_clears_variables(self):
        engine = make_engine("u:(my name is _): Hi $name.\nu:(hello): hi\n")
        engine.process_input("my name is Alice")
        assert "name" in engine.variables
        engine.reset()
        assert engine.variables == {}

    def test_state_returns_to_running_after_interrupt(self):
        engine = make_engine("u:([stop cancel reset quit]): ok.\nu:(hello): hi\n")
        engine.process_input("stop")
        assert engine.state == EngineState.RUNNING


# ========== Integration Test ==========

class TestIntegration:
    def test_sample_script_loads(self):
        """The sample_script.txt must load successfully."""
        script_path = os.path.join(os.path.dirname(__file__), "sample_script.txt")
        if not os.path.isfile(script_path):
            pytest.skip("sample_script.txt not found")
        engine = DialogEngine(filename=script_path)
        assert engine.is_loaded
        assert len(engine.top_rules) > 0
        # Should have some non-fatal errors (deliberate syntax errors in sample)
        fatal_errors = [e for e in engine.parse_errors if e.fatal]
        assert len(fatal_errors) == 0

    def test_sample_script_greeting(self):
        script_path = os.path.join(os.path.dirname(__file__), "sample_script.txt")
        if not os.path.isfile(script_path):
            pytest.skip("sample_script.txt not found")
        engine = DialogEngine(filename=script_path)
        result = engine.process_input("hello")
        assert result["matched"]
        assert result["response"] in ["hi", "hello", "what up", "sup"]

    def test_sample_script_name_capture(self):
        script_path = os.path.join(os.path.dirname(__file__), "sample_script.txt")
        if not os.path.isfile(script_path):
            pytest.skip("sample_script.txt not found")
        engine = DialogEngine(filename=script_path)
        engine.process_input("my name is Charlie")
        result = engine.process_input("what is my name")
        assert "Charlie" in result["response"]


if __name__ == "__main__":
    import pytest as _pytest
    _pytest.main([__file__, "-v"])
