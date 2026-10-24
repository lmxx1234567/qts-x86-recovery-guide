# Repository guidance

This repository is a practical guide for readers installing, recovering and maintaining QTS on generic x86 hardware.

- Organize guidance around applicability and prerequisites, steps, verification, troubleshooting and recovery. Explain what readers should do and how to recognize success; omit participant narration, implementation chronology and tool-session details.
- Preserve necessary safety and compatibility boundaries in actionable language. Never invent test results or compatibility. Identify example mappings and explain how readers can calibrate them; do not substitute stories about who confirmed or guessed them.
- Use English figures in English documents. Put Chinese UI captures and captions on a separately named Chinese page and link to it clearly. Distinguish real screenshots from illustrative renders or simulated states.
- Commit only files with a reader or maintenance purpose. Keep usable tools, relevant regression tests, finished figures and source assets where they serve that purpose. Exclude one-off rendering/debug scripts, sampling output, private logs and author working files; do not remove useful functionality just to reduce file count.
- When editing, check references across the whole repository: relative links and headings, command/tool paths, image captions and language, and references to removed files. Inspect text and figures for private identifiers or credentials. Run relevant checks and `python3 -m unittest discover -s tests -v`; distinguish offline checks from hardware validation.
- Keep coverage tables and review/test summaries in the PR description rather than the user guide. Follow [CONTRIBUTING.md](CONTRIBUTING.md) for sanitizing public reports.
