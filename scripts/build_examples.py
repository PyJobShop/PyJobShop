"""
Execute example notebooks into Markdown for the Zensical docs build.

This mirrors the old nbsphinx execution behaviour as a pre-build step: each
notebook is run, and its outputs are captured under docs/source/examples/.
Set SKIP_NOTEBOOKS=1 to convert without executing for faster local builds.

This is a temporary workaround. Once Zensical supports the mkdocs-jupyter
plugin natively, notebooks can be rendered directly and this script removed.
Tracked upstream at https://github.com/zensical/backlog/issues/9.
"""

import os
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).parent.parent
EXAMPLES_SRC = REPO / "examples"
EXAMPLES_OUT = REPO / "docs" / "source" / "examples"

NUMERIC_REFERENCE = re.compile(r"(?<!\\)\[(\d+(?:\s*[-,]\s*\d+)+)\](?!\()")
TRUTHY_ENV = {"1", "true", "yes", "on"}


def _fence_indented_blocks(markdown: str) -> str:
    """
    Convert nbconvert's indented output blocks to fenced blocks.

    Zensical checks link references inside indented blocks. Fenced blocks avoid
    false unresolved-link warnings for reprs containing strings like "[0]".
    """
    lines = markdown.splitlines()
    out = []
    in_fence = False
    idx = 0

    while idx < len(lines):
        line = lines[idx]
        if line.startswith("```"):
            in_fence = not in_fence
            out.append(line)
            idx += 1
            continue

        if not in_fence and line.startswith("    ") and line.strip():
            out.append("```text")

            while idx < len(lines):
                current = lines[idx]
                next_line = lines[idx + 1] if idx + 1 < len(lines) else ""

                if current.startswith("    "):
                    out.append(current[4:])
                    idx += 1
                elif not current.strip() and next_line.startswith("    "):
                    out.append("")
                    idx += 1
                else:
                    break

            out.append("```")
            continue

        out.append(line)
        idx += 1

    return "\n".join(out) + ("\n" if markdown.endswith("\n") else "")


def _escape_numeric_references(markdown: str) -> str:
    lines = markdown.splitlines()
    out = []
    in_fence = False

    for line in lines:
        if line.startswith("```"):
            in_fence = not in_fence

        if not in_fence:
            line = NUMERIC_REFERENCE.sub(r"\\[\1\\]", line)

        out.append(line)

    return "\n".join(out) + ("\n" if markdown.endswith("\n") else "")


def _post_process(markdown: str) -> str:
    markdown = _fence_indented_blocks(markdown)
    return _escape_numeric_references(markdown)


def main() -> None:
    EXAMPLES_OUT.mkdir(parents=True, exist_ok=True)
    skip_execution = os.getenv("SKIP_NOTEBOOKS", "").lower() in TRUTHY_ENV

    for notebook in sorted(EXAMPLES_SRC.glob("*.ipynb")):
        stem = notebook.stem
        cmd = [
            sys.executable,
            "-m",
            "jupyter",
            "nbconvert",
            "--to",
            "markdown",
            "--output-dir",
            str(EXAMPLES_OUT),
        ]

        if not skip_execution:
            cmd.append("--execute")

        cmd.append(str(notebook))

        suffix = " (without execution)" if skip_execution else ""
        print(f"Converting {notebook.name}{suffix}")
        subprocess.run(cmd, check=True)

        markdown = EXAMPLES_OUT / f"{stem}.md"
        markdown.write_text(_post_process(markdown.read_text()))


if __name__ == "__main__":
    main()
