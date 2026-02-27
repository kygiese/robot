"""
Dialog Engine for TangoChat-style script files.

Parses and runs conversations from TangoChat scripts. Supports:
- u:, u1:, u2:, ... rule levels with scoped pattern matching
- Bracket choices [a b c "two words"] in patterns and outputs
- Definitions ~name: [...] usable in patterns and outputs
- Variable capture with _varname or anonymous _ (mapped via output $vars)
- Action tags <nod> <shake> <raise> <dance> executed in background
- Case-insensitive, punctuation-tolerant matching
- Safety interrupt on stop/cancel/reset/quit
- Explicit state machine: IDLE -> RUNNING -> INTERRUPTED
"""

import re
import random
import time
import threading
import queue
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Tuple
from enum import Enum


# ========== State Machine ==========

class EngineState(Enum):
    IDLE = "IDLE"
    RUNNING = "RUNNING"
    INTERRUPTED = "INTERRUPTED"


# ========== Data Classes ==========

@dataclass
class ParseError:
    filename: str
    line_number: int
    category: str
    message: str
    fatal: bool

    def __str__(self):
        severity = "FATAL" if self.fatal else "WARNING"
        return f"{self.filename}:{self.line_number}: [{severity}] {self.category}: {self.message}"


@dataclass
class Rule:
    level: int
    pattern: str
    output: str
    subrules: List['Rule'] = field(default_factory=list)
    source_line: int = 0


# ========== Dialog Engine ==========

class DialogEngine:
    """
    TangoChat-style dialog engine with state machine and action tag support.

    State machine:
      IDLE      - no script loaded or after interrupt/reset
      RUNNING   - actively processing conversation
      INTERRUPTED - safety interrupt in progress (clears scope)
    """

    MAX_SCOPE_LEVEL = 6
    SAFETY_WORDS = {'stop', 'cancel', 'reset', 'quit'}

    def __init__(self, filename=None, robot_control=None):
        self.filename = filename
        self.robot_control = robot_control

        self.definitions: Dict[str, List[str]] = {}
        self.top_rules: List[Rule] = []
        self.variables: Dict[str, str] = {}

        # State machine
        self.state = EngineState.IDLE
        self.active_subrules: List[Rule] = []
        self.active_level: int = 0

        self.parse_errors: List[ParseError] = []
        self.is_loaded = False

        # Action execution - background queue with interrupt support
        self._action_queue: queue.Queue = queue.Queue()
        self._interrupt_flag = threading.Event()
        self._action_thread = threading.Thread(
            target=self._action_worker, daemon=True, name="dialog-action-worker"
        )
        self._action_thread.start()

        if filename:
            self.load(filename)

    # ========== Script Loading ==========

    def load(self, filename: str) -> bool:
        """Load and parse a TangoChat script file. Returns True on success."""
        self.filename = filename
        self.definitions = {}
        self.top_rules = []
        self.parse_errors = []
        self.is_loaded = False
        self.state = EngineState.IDLE

        try:
            with open(filename, 'r') as f:
                lines = f.readlines()
        except IOError as e:
            self._add_error(0, "FILE_ERROR", str(e), fatal=True)
            return False

        self._parse_lines(lines)

        if not self.top_rules:
            self._add_error(0, "NO_RULES",
                            "No valid top-level u: rules found", fatal=True)
            return False

        self.is_loaded = True
        self.state = EngineState.RUNNING
        return True

    def _parse_lines(self, lines: list):
        """Parse all script lines into definitions and rules."""
        parsed_rules: List[Rule] = []

        for lineno, raw_line in enumerate(lines, 1):
            # Strip comments
            if '#' in raw_line:
                raw_line = raw_line[:raw_line.index('#')]
            line = raw_line.strip()

            if not line:
                continue

            # Definition: ~name: [item1 item2 ...]
            def_match = re.match(r'^~(\w+)\s*:\s*(.+)$', line)
            if def_match:
                name = def_match.group(1)
                content = def_match.group(2).strip()
                items = self._parse_bracket_list(content, lineno)
                if items is not None:
                    self.definitions[name] = items
                else:
                    self._add_error(lineno, "SYNTAX_ERROR",
                                    f"Invalid definition syntax: {line}", fatal=False)
                continue

            # Rule: u[N]: (pattern): output
            rule = self._parse_rule(line, lineno)
            if rule is not None:
                parsed_rules.append(rule)
            else:
                self._add_error(lineno, "SYNTAX_ERROR",
                                f"Cannot parse line: {line}", fatal=False)

        self._build_hierarchy(parsed_rules)

    def _parse_bracket_list(self, content: str, lineno: int) -> Optional[List[str]]:
        """Parse [a b c "two words"] into a list of strings."""
        content = content.strip()
        if not content.startswith('['):
            return None

        depth = 0
        end = -1
        for i, ch in enumerate(content):
            if ch == '[':
                depth += 1
            elif ch == ']':
                depth -= 1
                if depth == 0:
                    end = i
                    break

        if end == -1:
            self._add_error(lineno, "SYNTAX_ERROR",
                            f"Unmatched '[' in: {content}", fatal=False)
            return None

        inner = content[1:end]
        return self._split_items(inner)

    @staticmethod
    def _split_items(text: str) -> List[str]:
        """Split space-separated items, respecting quoted strings."""
        items = []
        current = ''
        in_quotes = False
        for ch in text:
            if ch == '"':
                in_quotes = not in_quotes
            elif ch in (' ', '\t') and not in_quotes:
                if current:
                    items.append(current)
                    current = ''
            else:
                current += ch
        if current:
            items.append(current)
        return items

    def _parse_rule(self, line: str, lineno: int) -> Optional[Rule]:
        """Parse a rule line: u[N]: (pattern): output"""
        m = re.match(r'^(u(\d*))\s*:\s*(.+)$', line)
        if not m:
            return None

        level = int(m.group(2)) if m.group(2) else 0
        rest = m.group(3).strip()

        pattern, output = self._split_pattern_output(rest, lineno)
        if pattern is None:
            return None

        return Rule(level=level, pattern=pattern, output=output, source_line=lineno)

    def _split_pattern_output(self, text: str,
                               lineno: int) -> Tuple[Optional[str], Optional[str]]:
        """Split 'text' into (pattern, output) where text is '(pattern): output'."""
        text = text.strip()

        if not text.startswith('('):
            self._add_error(lineno, "SYNTAX_ERROR",
                            f"Pattern must start with '(': {text}", fatal=False)
            return None, None

        depth = 0
        end = -1
        for i, ch in enumerate(text):
            if ch == '(':
                depth += 1
            elif ch == ')':
                depth -= 1
                if depth == 0:
                    end = i
                    break

        if end == -1:
            self._add_error(lineno, "SYNTAX_ERROR",
                            f"Unmatched '(' in: {text}", fatal=False)
            return None, None

        pattern = text[1:end]
        rest = text[end + 1:].strip()

        if not rest.startswith(':'):
            self._add_error(lineno, "SYNTAX_ERROR",
                            f"Expected ':' after pattern in: {text}", fatal=False)
            return None, None

        output = rest[1:].strip()
        return pattern, output

    def _build_hierarchy(self, rules: List[Rule]):
        """Build rule hierarchy from flat list using rule levels."""
        stack: List[Tuple[int, Rule]] = []

        for rule in rules:
            if rule.level == 0:
                self.top_rules.append(rule)
                stack = [(0, rule)]
            else:
                # Pop until we find a parent with level = rule.level - 1
                while stack and stack[-1][0] >= rule.level:
                    stack.pop()

                if stack:
                    stack[-1][1].subrules.append(rule)
                    stack.append((rule.level, rule))
                else:
                    self._add_error(
                        rule.source_line, "ORPHAN_RULE",
                        f"u{rule.level}: has no parent u{rule.level - 1}: rule",
                        fatal=False
                    )
                    # Demote to top-level as fallback
                    self.top_rules.append(rule)
                    stack = [(0, rule)]

    def _add_error(self, lineno: int, category: str, message: str, fatal: bool):
        """Record a parse error and print it."""
        err = ParseError(
            filename=self.filename or "<unknown>",
            line_number=lineno,
            category=category,
            message=message,
            fatal=fatal
        )
        self.parse_errors.append(err)
        print(str(err))

    # ========== Pattern Matching ==========

    @staticmethod
    def _normalize_input(text: str) -> str:
        """Normalize user input: strip basic punctuation and extra whitespace."""
        text = re.sub(r'[.,!?;:]', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def _pattern_to_regex(self, pattern: str) -> Tuple[str, List[str]]:
        """Convert a pattern string to (regex_str, capture_names)."""
        capture_names: List[str] = []
        regex = self._build_pattern_regex(pattern.strip(), capture_names)
        return r'^\s*' + regex + r'\s*$', capture_names

    def _build_pattern_regex(self, pattern: str, capture_names: List[str]) -> str:
        """Recursively build a regex string from a pattern."""
        parts: List[str] = []
        i = 0

        while i < len(pattern):
            ch = pattern[i]

            # Whitespace between tokens
            if ch in (' ', '\t'):
                while i < len(pattern) and pattern[i] in (' ', '\t'):
                    i += 1
                if parts and parts[-1] != r'\s+':
                    parts.append(r'\s+')
                continue

            # Bracket choice [a b c "two words"]
            if ch == '[':
                depth = 1
                j = i + 1
                while j < len(pattern) and depth > 0:
                    if pattern[j] == '[':
                        depth += 1
                    elif pattern[j] == ']':
                        depth -= 1
                    j += 1
                if depth != 0:
                    parts.append(re.escape(pattern[i:]))
                    break
                content = pattern[i + 1:j - 1]
                items = self._split_items(content)
                alts = [re.escape(item.lower()) for item in items]
                parts.append('(?:' + '|'.join(alts) + ')')
                i = j
                continue

            # Definition ~name
            if ch == '~':
                m = re.match(r'~(\w+)', pattern[i:])
                if m:
                    name = m.group(1)
                    if name in self.definitions:
                        alts = [re.escape(item.lower())
                                for item in self.definitions[name]]
                        parts.append('(?:' + '|'.join(alts) + ')')
                    else:
                        parts.append(re.escape('~' + name))
                    i += len(m.group(0))
                    continue

            # Wildcard capture _varname or anonymous _
            if ch == '_':
                m = re.match(r'_(\w+)', pattern[i:])
                if m and m.group(1):
                    varname = m.group(1)
                    capture_names.append(varname)
                    parts.append(r'(.+?)')
                    i += len(m.group(0))
                else:
                    capture_names.append(f'_{len(capture_names)}')
                    parts.append(r'(.+?)')
                    i += 1
                continue

            # Star wildcard *
            if ch == '*':
                capture_names.append(f'_star{len(capture_names)}')
                parts.append(r'(.*?)')
                i += 1
                continue

            # Quoted phrase "two words"
            if ch == '"':
                j = pattern.find('"', i + 1)
                if j == -1:
                    j = len(pattern)
                phrase = pattern[i + 1:j]
                parts.append(re.escape(phrase.lower()))
                i = j + 1
                continue

            # Literal word
            j = i
            while j < len(pattern) and pattern[j] not in (' ', '\t', '[', '~', '_', '*', '"'):
                j += 1
            word = pattern[i:j].lower()
            if word:
                parts.append(re.escape(word))
            i = j

        # Remove trailing whitespace separator
        while parts and parts[-1] == r'\s+':
            parts.pop()

        return ''.join(parts)

    def _match_rule(self, rule: Rule,
                    normalized_input: str) -> Optional[Tuple[List[str], List[str]]]:
        """
        Try to match rule against normalized input.
        Returns (capture_names, capture_values) if matched, else None.
        """
        try:
            regex_str, capture_names = self._pattern_to_regex(rule.pattern)
            m = re.match(regex_str, normalized_input, re.IGNORECASE)
            if m:
                values = [g.strip() if g else '' for g in m.groups()]
                return capture_names, values
        except re.error as e:
            print(f"WARNING: Regex error for pattern '{rule.pattern}' "
                  f"(line {rule.source_line}): {e}")
        return None

    # ========== Output Processing ==========

    def _process_output(self, output: str,
                        capture_names: List[str],
                        capture_values: List[str]) -> Tuple[str, List[str]]:
        """
        Process output string:
        - Expand ~name definitions with random choice
        - Expand [a b c] bracket choices with random selection
        - Store captures into variables (named: directly; anonymous: positional)
        - Expand $varname references (returns "I don't know" if unset)
        - Extract and strip action tags

        Returns (spoken_text, action_tags_list).
        """
        # Expand ~name definitions in output
        def expand_def(text):
            def replace(m):
                name = m.group(1)
                if name in self.definitions:
                    return random.choice(self.definitions[name])
                return m.group(0)
            return re.sub(r'~(\w+)', replace, text)

        output = expand_def(output)

        # Expand bracket choices [a b c]
        def expand_brackets(text):
            result = text
            while '[' in result:
                start = result.find('[')
                depth = 0
                end = -1
                for idx in range(start, len(result)):
                    if result[idx] == '[':
                        depth += 1
                    elif result[idx] == ']':
                        depth -= 1
                        if depth == 0:
                            end = idx
                            break
                if end == -1:
                    break
                content = result[start + 1:end]
                items = self._split_items(content)
                choice = random.choice(items) if items else ''
                result = result[:start] + choice + result[end + 1:]
            return result

        output = expand_brackets(output)

        # Assign captures to variables
        # Named captures (_varname) → stored directly as $varname
        # Anonymous captures (_N/_starN) → mapped positionally to $xxx in output
        unnamed_values: List[str] = []
        for name, val in zip(capture_names, capture_values):
            if re.match(r'^(_\d+|_star\d+)$', name):
                unnamed_values.append(val)
            else:
                # Named capture
                self.variables[name] = val

        if unnamed_values:
            # Find $varname references in output (in order of appearance)
            output_var_refs = re.findall(r'\$(\w+)', output)
            for idx, val in enumerate(unnamed_values):
                if idx < len(output_var_refs):
                    self.variables[output_var_refs[idx]] = val

        # Expand $varname references
        def expand_var(m):
            varname = m.group(1)
            return self.variables.get(varname, "I don't know")

        output = re.sub(r'\$(\w+)', expand_var, output)

        # Extract action tags before removing them
        action_tags = re.findall(r'<[^>]+>', output)

        # Remove action tags from spoken text
        text = re.sub(r'<[^>]+>', '', output)
        text = re.sub(r'\s+', ' ', text).strip()

        return text, action_tags

    # ========== Action Tag Execution ==========

    def _action_worker(self):
        """Background worker thread: dequeues and executes action functions."""
        while True:
            try:
                action_func = self._action_queue.get(timeout=0.2)
                if action_func is None:
                    break
                if not self._interrupt_flag.is_set():
                    try:
                        action_func()
                    except Exception as e:
                        print(f"Action execution error: {e}")
                self._action_queue.task_done()
            except queue.Empty:
                continue

    def _queue_action(self, action_func):
        """Queue an action for background execution."""
        self._action_queue.put(action_func)

    def _execute_action_tags(self, action_tags: List[str]):
        """Dispatch all action tags to the background queue."""
        for tag in action_tags:
            self._dispatch_action(tag)

    def _dispatch_action(self, tag: str):
        """Parse and dispatch a single action tag to the queue."""
        content = tag[1:-1].strip().lower()  # strip < >

        known_actions = {'nod', 'shake', 'raise', 'dance'}
        if content not in known_actions:
            print(f"WARNING: Unknown action tag ignored: {tag}")
            return

        if not self.robot_control:
            return

        rc = self.robot_control
        interrupt = self._interrupt_flag

        if content == 'nod':
            def do_nod():
                # Tilt down, pause, tilt up, pause, center
                rc.head_tilt(-60)
                if interrupt.wait(timeout=0.4):
                    return
                rc.head_tilt(60)
                if interrupt.wait(timeout=0.4):
                    return
                rc.head_tilt(0)
            self._queue_action(do_nod)

        elif content == 'shake':
            def do_shake():
                # Pan left, pause, pan right, pause, center
                rc.head_pan(-60)
                if interrupt.wait(timeout=0.4):
                    return
                rc.head_pan(60)
                if interrupt.wait(timeout=0.4):
                    return
                rc.head_pan(0)
            self._queue_action(do_shake)

        elif content == 'raise':
            def do_raise():
                # Raise right shoulder servo up, hold, return to neutral
                if hasattr(rc, 'raise_arm'):
                    rc.raise_arm()
                else:
                    # Fallback: tilt head up as a visible gesture
                    rc.head_tilt(70)
                    if interrupt.wait(timeout=1.0):
                        return
                    rc.head_tilt(0)
            self._queue_action(do_raise)

        elif content == 'dance':
            def do_dance():
                # Rotate in place: left ~90°, right ~90°, return to start
                # Uses waist if available, otherwise wheel-based in-place rotation
                if hasattr(rc, 'waist'):
                    rc.waist(-70)
                    if interrupt.wait(timeout=0.7):
                        rc.waist(0)
                        return
                    rc.waist(70)
                    if interrupt.wait(timeout=0.7):
                        rc.waist(0)
                        return
                    rc.waist(0)
                else:
                    # Wheel-based rotation
                    rc.drive(-60, 60)
                    if interrupt.wait(timeout=0.6):
                        rc.stop()
                        return
                    rc.drive(60, -60)
                    if interrupt.wait(timeout=0.6):
                        rc.stop()
                        return
                    rc.stop()
            self._queue_action(do_dance)

    def _interrupt_actions(self):
        """Interrupt all ongoing actions and stop the robot."""
        self._interrupt_flag.set()

        # Drain the action queue
        while not self._action_queue.empty():
            try:
                self._action_queue.get_nowait()
                self._action_queue.task_done()
            except queue.Empty:
                break

        # Stop the robot immediately
        if self.robot_control:
            try:
                self.robot_control.stop()
            except Exception:
                pass

        # Clear interrupt flag after a brief delay to allow actions to notice it
        def clear_flag():
            time.sleep(0.15)
            self._interrupt_flag.clear()

        threading.Thread(target=clear_flag, daemon=True).start()

    # ========== Main Input Processing ==========

    def process_input(self, user_input: str) -> dict:
        """
        Process a user input string and return a response dict:
          {
            "response": str,       # text to speak
            "action_tags": list,   # raw action tags found
            "matched": bool,       # whether any rule matched
            "state": str           # current engine state name
          }
        """
        if not self.is_loaded:
            return {
                "response": "No script loaded.",
                "action_tags": [],
                "matched": False,
                "state": self.state.value
            }

        normalized = self._normalize_input(user_input)

        # Safety interrupt: check for stop/cancel/reset/quit words
        input_words = set(normalized.split())
        if input_words & self.SAFETY_WORDS:
            self._interrupt_actions()
            self._reset_scope()
            self.state = EngineState.INTERRUPTED

            # Still try to get a response from the script for this input
            result = self._find_and_apply_rule(normalized)
            self.state = EngineState.RUNNING
            if result:
                return result
            return {
                "response": "OK. Stopping.",
                "action_tags": [],
                "matched": True,
                "state": EngineState.RUNNING.value
            }

        self.state = EngineState.RUNNING
        result = self._find_and_apply_rule(normalized)
        if result:
            return result

        return {
            "response": "I don't understand.",
            "action_tags": [],
            "matched": False,
            "state": self.state.value
        }

    def _find_and_apply_rule(self, normalized: str) -> Optional[dict]:
        """
        Try to find and apply a matching rule. Returns response dict or None.

        Scope order: active subrules first, then top-level rules.
        """
        # Try active subrules first (current scope)
        if self.active_subrules:
            for rule in self.active_subrules:
                match_result = self._match_rule(rule, normalized)
                if match_result is not None:
                    capture_names, capture_values = match_result
                    text, action_tags = self._process_output(
                        rule.output, capture_names, capture_values
                    )
                    self._execute_action_tags(action_tags)

                    # Advance scope if rule has subrules and within depth limit
                    if rule.subrules and rule.level < self.MAX_SCOPE_LEVEL:
                        self.active_subrules = rule.subrules
                        self.active_level = rule.level + 1

                    return self._make_response(text, action_tags, rule.level)

        # Try top-level rules (always available)
        for rule in self.top_rules:
            match_result = self._match_rule(rule, normalized)
            if match_result is not None:
                capture_names, capture_values = match_result
                text, action_tags = self._process_output(
                    rule.output, capture_names, capture_values
                )
                self._execute_action_tags(action_tags)

                # A top-level match clears previous scope and starts new one
                if rule.subrules:
                    self.active_subrules = rule.subrules
                    self.active_level = 1
                else:
                    self._reset_scope()

                return self._make_response(text, action_tags, rule.level)

        return None

    def _make_response(self, text: str, action_tags: List[str], level: int) -> dict:
        return {
            "response": text,
            "action_tags": action_tags,
            "matched": True,
            "rule_level": level,
            "state": self.state.value
        }

    def _reset_scope(self):
        """Reset to top-level scope (clear active subrules)."""
        self.active_subrules = []
        self.active_level = 0

    # ========== Public Interface ==========

    def reset(self):
        """Reset conversation state (variables, scope, state machine)."""
        self.variables = {}
        self._reset_scope()
        if self.is_loaded:
            self.state = EngineState.RUNNING

    def get_status(self) -> dict:
        """Return current engine status."""
        return {
            "loaded": self.is_loaded,
            "filename": self.filename,
            "state": self.state.value,
            "rule_count": len(self.top_rules),
            "active_scope_level": self.active_level,
            "variables": dict(self.variables),
            "errors": [str(e) for e in self.parse_errors]
        }

    def shutdown(self):
        """Shutdown the engine cleanly."""
        self._interrupt_actions()
        self._action_queue.put(None)  # Signal worker thread to stop
