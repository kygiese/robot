"""
Dialog Engine - TangoChat-style conversation system

Parses a script file and processes user input to produce:
  - Response text (for text-to-speech)
  - Action tags (for ActionRunner)

Script format:
  # comment
  ~name: [option1 option2 "multi word"]
  u: (pattern) : output text <action>
      u1: (sub pattern) : sub output
          u2: (deep pattern) : deep output
"""

import re
import random


class ParseError:
    """Represents a script parsing error."""

    def __init__(self, filename, line_num, category, message, fatal=False):
        self.filename = filename
        self.line_num = line_num
        self.category = category
        self.message = message
        self.fatal = fatal

    def __str__(self):
        severity = "FATAL" if self.fatal else "WARNING"
        return (
            f"{self.filename}:{self.line_num}: [{severity}] "
            f"{self.category}: {self.message}"
        )


class Rule:
    """A single conversation rule with pattern, output, and optional subrules."""

    def __init__(self, level, pattern_str, output_str, line_num):
        self.level = level        # 0=u:, 1=u1:, 2=u2:, etc.
        self.pattern_str = pattern_str
        self.output_str = output_str
        self.line_num = line_num
        self.subrules = []        # nested rules at (level+1)


class DialogEngine:
    """
    TangoChat-style dialog engine.

    Usage:
        engine = DialogEngine()
        if engine.load_script("script.bot"):
            response, actions = engine.process_input("hello there")
    """

    MAX_DEPTH = 6  # max nesting levels (u: through u5:, levels 0-5)

    def __init__(self):
        self.filename = None
        self.rules = []            # top-level u: rules
        self.definitions = {}      # ~name -> list[str]
        self.variables = {}        # captured variables ($name -> value)
        self.active_subrules = []  # currently active u1: (or u2:) rules
        self.errors = []
        self._loaded = False

    # ------------------------------------------------------------------ #
    # Loading / Parsing                                                    #
    # ------------------------------------------------------------------ #

    def load_script(self, filename):
        """
        Load and parse a TangoChat script file.

        Returns True on success, False on fatal error.
        Non-fatal errors are printed and logged to self.errors.
        """
        self.filename = filename
        self.rules = []
        self.definitions = {}
        self.errors = []
        self._loaded = False

        try:
            with open(filename, "r") as fh:
                lines = fh.readlines()
        except OSError as exc:
            err = ParseError(filename, 0, "FILE_ERROR", str(exc), fatal=True)
            self.errors.append(err)
            print(err)
            return False

        self._parse_lines(lines)

        for err in self.errors:
            if err.fatal:
                return False

        if not self.rules:
            err = ParseError(
                filename, 0, "NO_RULES",
                "No valid top-level u: rules found", fatal=True
            )
            self.errors.append(err)
            print(err)
            return False

        self._loaded = True
        return True

    def _parse_lines(self, lines):
        """Parse all script lines, populating self.rules and self.definitions."""
        # rule_stack[level] = most-recently-seen Rule at that nesting level
        rule_stack = {}

        for line_num, raw_line in enumerate(lines, start=1):
            line = raw_line.rstrip()

            # Strip inline comments
            comment_pos = line.find("#")
            if comment_pos >= 0:
                line = line[:comment_pos].rstrip()

            # Skip blank lines
            if not line.strip():
                continue

            stripped = line.strip()

            # ---- Definition: ~name: [ options ] -------------------------
            def_match = re.match(r"^~(\w+)\s*:\s*\[(.+)\]", stripped)
            if def_match:
                name = def_match.group(1)
                opts = self._parse_bracket_options(def_match.group(2))
                if opts:
                    self.definitions[name] = opts
                else:
                    self._warn(line_num, "INVALID_DEFINITION",
                               f"Empty definition for ~{name}")
                continue

            # ---- Rule: u:(pattern):output  or  u1:(pattern):output  ----
            rule_match = re.match(
                r"^(u(\d*))\s*:\s*\(([^)]*)\)\s*:\s*(.*)", stripped
            )
            if rule_match:
                level_str = rule_match.group(2)   # '', '1', '2', ...
                pattern_str = rule_match.group(3).strip()
                output_str = rule_match.group(4).strip()
                level = 0 if level_str == "" else int(level_str)

                if not output_str:
                    self._warn(line_num, "EMPTY_OUTPUT",
                               f"Rule u{level_str}: has empty output — skipping")
                    continue

                # Guard: enforce maximum nesting depth
                if level >= self.MAX_DEPTH:
                    self._warn(line_num, "MAX_DEPTH",
                               f"u{level}: exceeds max depth {self.MAX_DEPTH} — skipping")
                    continue

                # Guard: detect unbalanced brackets in output
                if not self._brackets_balanced(output_str):
                    self._warn(line_num, "UNBALANCED_BRACKET",
                               f"Unbalanced brackets in output — skipping")
                    continue

                rule = Rule(level, pattern_str, output_str, line_num)

                if level == 0:
                    self.rules.append(rule)
                    rule_stack = {0: rule}
                else:
                    parent_level = level - 1
                    if parent_level in rule_stack:
                        rule_stack[parent_level].subrules.append(rule)
                        rule_stack[level] = rule
                        # Discard any deeper stale entries
                        for k in list(rule_stack):
                            if k > level:
                                del rule_stack[k]
                    else:
                        self._warn(line_num, "ORPHAN_RULE",
                                   f"u{level}: rule has no parent — skipping")
                continue

            # ---- Unrecognized line --------------------------------------
            self._warn(line_num, "UNRECOGNIZED_LINE",
                       f"Cannot parse: {stripped[:60]}")

    def _warn(self, line_num, category, message, fatal=False):
        err = ParseError(self.filename, line_num, category, message, fatal)
        self.errors.append(err)
        print(err)

    @staticmethod
    def _brackets_balanced(text):
        """Return True if square brackets in *text* are properly nested."""
        depth = 0
        for ch in text:
            if ch == "[":
                depth += 1
            elif ch == "]":
                depth -= 1
                if depth < 0:
                    return False
        return depth == 0

    # ------------------------------------------------------------------ #
    # Conversation processing                                              #
    # ------------------------------------------------------------------ #

    def process_input(self, user_input):
        """
        Match user_input against active rules and return (response, actions).

        Scope rules:
        - If a u: rule matches, its u1: subrules become the active scope.
        - If a u1: rule matches (in scope), its u2: subrules become active.
        - Matching a new u: rule always clears any previous scope.

        Returns (response_text, actions_list).
        Returns (None, []) when no rule matches.
        """
        if not self._loaded:
            return ("Dialog engine not loaded.", [])

        normalized = self._normalize_input(user_input)

        # Try active subrules first
        if self.active_subrules:
            for rule in self.active_subrules:
                captures = self._match_pattern(normalized, rule.pattern_str)
                if captures is not None:
                    self._assign_captures(captures, rule.output_str)
                    response, actions = self._build_output(rule.output_str)
                    self.active_subrules = rule.subrules
                    return (response, actions)

        # Fall through to top-level rules
        for rule in self.rules:
            captures = self._match_pattern(normalized, rule.pattern_str)
            if captures is not None:
                self._assign_captures(captures, rule.output_str)
                response, actions = self._build_output(rule.output_str)
                # New top-level match: replace scope with this rule's subrules
                self.active_subrules = rule.subrules
                return (response, actions)

        return (None, [])

    def reset(self):
        """Reset conversational state (variables and scope) without unloading rules."""
        self.variables = {}
        self.active_subrules = []

    # ------------------------------------------------------------------ #
    # Pattern matching helpers                                             #
    # ------------------------------------------------------------------ #

    def _normalize_input(self, text):
        """Lowercase and strip basic punctuation from user input."""
        text = text.lower()
        text = re.sub(r"[.,!?;:'\"-]", "", text)
        return " ".join(text.split())

    def _match_pattern(self, normalized_input, pattern_str):
        """
        Try to match normalized_input against pattern_str.

        Returns a dict of positional captures {'_cap_0': text, ...},
        or None on no match.
        """
        regex, n_caps = self._pattern_to_regex(pattern_str)
        if regex is None:
            return None
        try:
            m = re.fullmatch(regex, normalized_input, re.IGNORECASE)
        except re.error:
            return None
        if m:
            return {f"_cap_{i}": (g or "").strip()
                    for i, g in enumerate(m.groups()) if i < n_caps}
        return None

    def _parse_bracket_options(self, options_str):
        """Parse 'opt1 opt2 "multi word"' into a list of strings."""
        options = []
        for m in re.finditer(r'"([^"]+)"|(\S+)', options_str):
            options.append(m.group(1) if m.group(1) is not None else m.group(2))
        return options

    def _tokenize_pattern(self, pattern_str):
        """
        Tokenize a pattern string into a list of tokens:
        '[bracketed group]', '_', '*', '"quoted phrase"', or literal words.

        Handles nested brackets (from ~name expansion inside []) via depth
        tracking. Top-level ~name is expanded directly to a bracket group.
        Quoted phrases ("multi word") are treated as a single literal token.
        """
        tokens = []
        s = pattern_str.strip()
        i = 0
        while i < len(s):
            ch = s[i]
            if ch in " \t":
                i += 1
            elif ch == '"':
                # Quoted phrase — treat as a single literal token
                j = s.find('"', i + 1)
                if j == -1:
                    # Unmatched quote — consume rest of string
                    tokens.append(s[i + 1:])
                    break
                tokens.append(s[i + 1: j])
                i = j + 1
            elif ch == "[":
                # Depth-based scan for the matching closing bracket
                depth = 1
                j = i + 1
                while j < len(s) and depth > 0:
                    if s[j] == "[":
                        depth += 1
                    elif s[j] == "]":
                        depth -= 1
                    j += 1
                # Expand any ~name inside the brackets before storing
                inner = s[i + 1: j - 1]
                expanded_inner = self._expand_defs_inline(inner)
                tokens.append(f"[{expanded_inner}]")
                i = j
            elif ch == "~":
                # Standalone ~name — expand to a bracket group
                j = i + 1
                while j < len(s) and (s[j].isalnum() or s[j] == "_"):
                    j += 1
                name = s[i + 1: j]
                if name in self.definitions:
                    opts = self.definitions[name]
                    inner = " ".join(
                        f'"{o}"' if " " in o else o for o in opts
                    )
                    tokens.append(f"[{inner}]")
                i = j
            elif ch == "_":
                tokens.append("_")
                i += 1
            elif ch == "*":
                tokens.append("*")
                i += 1
            else:
                j = i
                while j < len(s) and s[j] not in " \t[]_*~\"":
                    j += 1
                if j > i:
                    tokens.append(s[i:j])
                i = max(j, i + 1)
        return [t for t in tokens if t]

    def _expand_defs_inline(self, text):
        """
        Replace ~name in *text* with the space-separated options from the
        definition.  Used when ~name appears inside a [bracket group].
        """
        def _replace(m):
            name = m.group(1)
            if name in self.definitions:
                opts = self.definitions[name]
                return " ".join(
                    f'"{o}"' if " " in o else o for o in opts
                )
            return m.group(0)
        return re.sub(r"~(\w+)", _replace, text)

    def _pattern_to_regex(self, pattern_str):
        """
        Convert a pattern string to a (regex_str, n_captures) tuple.
        Returns (None, 0) on error.
        """
        tokens = self._tokenize_pattern(pattern_str)
        parts = []
        n_caps = 0

        for token in tokens:
            if token == "_":
                parts.append(r"(.+?)")
                n_caps += 1
            elif token == "*":
                parts.append(r"(?:.*?)")
            elif token.startswith("[") and token.endswith("]"):
                opts = self._parse_bracket_options(token[1:-1])
                escaped = [re.escape(o) for o in opts]
                parts.append("(?:" + "|".join(escaped) + ")")
            else:
                parts.append(re.escape(token))

        if not parts:
            return (None, 0)

        # Allow flexible whitespace between tokens
        regex = r"\s*".join(parts)
        # Allow optional leading/trailing words for '*' at edges is handled
        # by the tokens themselves; here just return the built regex.
        return (regex, n_caps)

    # ------------------------------------------------------------------ #
    # Output processing helpers                                            #
    # ------------------------------------------------------------------ #

    def _assign_captures(self, captures, output_str):
        """
        Map positional captures (_cap_0, _cap_1, …) to the $variable names
        that appear in output_str (in order of first appearance).
        """
        var_names = list(dict.fromkeys(re.findall(r"\$(\w+)", output_str)))
        values = [captures[k] for k in sorted(captures)]
        for i, name in enumerate(var_names):
            if i < len(values):
                self.variables[name] = values[i]

    def _build_output(self, output_str):
        """
        Process an output string:
        1. Extract <action> tags.
        2. Expand ~name (random choice from definition).
        3. Expand [opt1 opt2 "multi word"] (random choice).
        4. Substitute $variable references.

        Returns (text, actions_list).
        """
        # 1. Extract action tags
        actions = re.findall(r"<(\w+)>", output_str)
        text = re.sub(r"<\w+>", "", output_str).strip()

        # 2. Expand ~name in output (random choice)
        def _expand_def(m):
            name = m.group(1)
            if name in self.definitions:
                return random.choice(self.definitions[name])
            return m.group(0)
        text = re.sub(r"~(\w+)", _expand_def, text)

        # 3. Expand [options] in output (random choice)
        def _expand_bracket(m):
            opts = self._parse_bracket_options(m.group(1))
            return random.choice(opts) if opts else ""
        text = re.sub(r"\[([^\]]+)\]", _expand_bracket, text)

        # 4. Substitute $variable references
        def _expand_var(m):
            name = m.group(1)
            return self.variables.get(name, "I don't know")
        text = re.sub(r"\$(\w+)", _expand_var, text)

        text = " ".join(text.split())
        return (text, actions)

