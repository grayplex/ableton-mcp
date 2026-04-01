---
phase: quick
plan: 260401-pil
type: execute
wave: 1
depends_on: []
files_modified:
  - MCP_Server/prompt/lexicon.py
  - MCP_Server/refinement/lexicon.py
  - MCP_Server/prompt/parser.py
autonomous: true
requirements: []
must_haves:
  truths:
    - "Both lexicon files document the English-only limitation prominently in module docstrings"
    - "Parser docstring explains that unrecognized non-English tokens fall through to raw_descriptors"
  artifacts:
    - path: "MCP_Server/prompt/lexicon.py"
      provides: "English-only limitation documented in module docstring"
      contains: "English-only"
    - path: "MCP_Server/refinement/lexicon.py"
      provides: "English-only limitation documented in module docstring"
      contains: "English-only"
    - path: "MCP_Server/prompt/parser.py"
      provides: "raw_descriptors fallback note for non-English input"
      contains: "raw_descriptors"
  key_links: []
---

<objective>
Document the English-only limitation of the prompt parser lexicon system.

Purpose: The prompt parser and both lexicons (prompt + refinement) only contain English terms.
Non-English input silently falls through to raw_descriptors with no warning or documentation.
This task adds clear documentation so users and future developers understand the limitation
and the raw_descriptors fallback behavior.

Output: Updated docstrings in lexicon.py (prompt), lexicon.py (refinement), and parser.py.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@MCP_Server/prompt/lexicon.py
@MCP_Server/refinement/lexicon.py
@MCP_Server/prompt/parser.py
@MCP_Server/prompt/schema.py
</context>

<tasks>

<task type="auto">
  <name>Task 1: Document English-only limitation in lexicons and parser</name>
  <files>MCP_Server/prompt/lexicon.py, MCP_Server/refinement/lexicon.py, MCP_Server/prompt/parser.py</files>
  <action>
Update the module-level docstrings in all three files to document the English-only limitation:

1. **MCP_Server/prompt/lexicon.py** — Add to the existing module docstring (after the normalization convention line):
   ```
   Language: English-only. All lookup tables contain English terms exclusively.
   Non-English input tokens will not match any signal and fall through to
   raw_descriptors in the parser. Adding multilingual aliases here would
   extend coverage without parser changes.
   ```

2. **MCP_Server/refinement/lexicon.py** — Add to the existing module docstring (after the "None fields" line):
   ```
   Language: English-only. All adjective keys are English. Non-English
   refinement terms will not match any entry.
   ```

3. **MCP_Server/prompt/parser.py** — Update the `classify_prompt` function docstring to note the fallback behavior. After the existing "Unrecognized tokens" line, add:
   ```
   Note: The lexicon is English-only. Non-English tokens (length > 2) are
   collected in raw_descriptors rather than being silently discarded, so
   downstream consumers can still surface them to the user or pass them
   to an LLM for interpretation.
   ```

Keep all changes to docstrings/comments only — no functional code changes.
  </action>
  <verify>
    <automated>cd I:/ableton-mcp && python -c "import MCP_Server.prompt.lexicon; import MCP_Server.refinement.lexicon; import MCP_Server.prompt.parser; print('imports ok')" && python -c "from MCP_Server.prompt.lexicon import __doc__ as d; assert 'English-only' in d, f'missing in prompt lexicon: {d[:200]}'; print('prompt lexicon: ok')" && python -c "from MCP_Server.refinement import lexicon; assert 'English-only' in lexicon.__doc__, 'missing in refinement lexicon'; print('refinement lexicon: ok')" && python -c "from MCP_Server.prompt.parser import classify_prompt; assert 'English-only' in classify_prompt.__doc__, 'missing in parser'; print('parser: ok')"</automated>
  </verify>
  <done>All three files have English-only limitation documented. Module imports still work. No functional changes.</done>
</task>

</tasks>

<verification>
- All three files import without error
- "English-only" appears in both lexicon module docstrings
- "raw_descriptors" fallback for non-English input is documented in parser
- Existing tests still pass: `cd I:/ableton-mcp && python -m pytest tests/test_prompt_phase42.py -x -q`
</verification>

<success_criteria>
- The English-only limitation is documented prominently enough that a developer reading lexicon.py or parser.py will see it without searching
- No functional code changes — docstrings/comments only
- All existing tests pass
</success_criteria>

<output>
After completion, create `.planning/quick/260401-pil-prompt-parser-is-english-only-document-t/260401-pil-SUMMARY.md`
</output>
