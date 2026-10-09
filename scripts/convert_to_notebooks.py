"""
Convert MyST Markdown tutorials to Jupyter notebooks and inject Colab/Kaggle badges.

Usage:
    python scripts/convert_to_notebooks.py [--dry-run]
    python scripts/convert_to_notebooks.py --inject-md-badges [--dry-run]

Default mode (used by generate-notebooks.yml). For each .md file in tutorials/
that has a kernelspec frontmatter:
  1. Convert to .ipynb via jupytext
  2. Replace {nma-video}/{nma-slides} directives with NMA code cells
     (scripts/nma_media.py)
  3. Inject a Colab + Kaggle badge markdown cell at position 0 in the .ipynb
  4. Write .ipynb to notebooks/<day_folder>/<tutorial_name>.ipynb
  The .md sources are never modified in this mode.

--inject-md-badges mode (used by publish-book.yml right before `myst build`):
  Insert Colab + Kaggle badge HTML into each kernelspec .md file (after the
  frontmatter) so badges appear on the rendered book page. This edits files
  in place, so only run it on a throwaway checkout (CI). Never commit the result.

Both modes first validate the content rules and exit non-zero on any violation:
  - No .ipynb files in tutorials/ (all content is authored as MyST .md)
  - Any .md with a {code-cell} directive must declare a kernelspec
  - {nma-video}/{nma-slides} directives must be valid (ids present, known
    options only, closed, no body)

The GitHub repo URL is read from myst.yml (project.github) so badge URLs update
automatically when the template is forked.

Both badge injection steps are idempotent — safe to re-run.
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

import yaml

from nma_media import expand_notebook, find_directives, validate_directive


TUTORIALS_DIR = Path("tutorials")
NOTEBOOKS_DIR = Path("notebooks")
MYST_CONFIG = Path("myst.yml")
NOTEBOOKS_BRANCH = "notebooks-branch"


def load_github_repo(myst_config: Path) -> str:
    """
    Read project.github from myst.yml and return 'org/repo' string.

    Example: 'https://github.com/neuromatch/course-template' -> 'neuromatch/course-template'
    """
    with myst_config.open() as fh:
        config = yaml.safe_load(fh)

    github_url = config.get("project", {}).get("github", "")
    if not github_url:
        raise ValueError("project.github is not set in myst.yml")

    github_url = github_url.rstrip("/")
    match = re.search(r"github\.com/(.+)", github_url)
    if not match:
        raise ValueError(f"Cannot parse GitHub repo from: {github_url}")

    return match.group(1)  # e.g. 'neuromatch/course-template'


def has_kernelspec(md_file: Path) -> bool:
    """Return True if the .md file has a kernelspec key in its YAML frontmatter."""
    content = md_file.read_text(encoding="utf-8")
    if not content.startswith("---"):
        return False

    end = content.find("---", 3)
    if end == -1:
        return False

    frontmatter_text = content[3:end]
    try:
        fm = yaml.safe_load(frontmatter_text)
    except yaml.YAMLError:
        return False

    return isinstance(fm, dict) and "kernelspec" in fm


FENCE_RE = re.compile(r"^(`{3,}|~{3,})(.*)$")


def has_code_cells(md_file: Path) -> bool:
    """
    Return True if the .md file contains a top-level {code-cell} directive.

    Code-cells shown as examples inside another fenced block (e.g. a
    ````markdown fence) don't count, so documentation pages can show the
    syntax without being treated as executable.
    """
    open_fence = None  # (char, length) of the fence we're currently inside
    for line in md_file.read_text(encoding="utf-8").splitlines():
        match = FENCE_RE.match(line)
        if not match:
            continue
        marker, info = match.group(1), match.group(2).strip()
        if open_fence is None:
            if info.startswith("{code-cell}"):
                return True
            open_fence = (marker[0], len(marker))
        elif marker[0] == open_fence[0] and len(marker) >= open_fence[1] and not info:
            open_fence = None
    return False


def validate_content() -> list[str]:
    """Check the Markdown-only content rules. Returns a list of violations."""
    errors = []
    for path in sorted(TUTORIALS_DIR.rglob("*.ipynb")):
        if ".ipynb_checkpoints" in path.parts:
            continue
        errors.append(
            f"{path}: .ipynb files are not allowed in tutorials/. Convert it with "
            f"`jupytext --to md:myst` and commit only the .md."
        )
    for path in sorted(TUTORIALS_DIR.rglob("*.md")):
        if has_code_cells(path) and not has_kernelspec(path):
            errors.append(
                f"{path}: contains {{code-cell}} blocks but no `kernelspec` in its "
                f"frontmatter, so it would get no notebook, badges, or JupyterLite button."
            )
        text = path.read_text(encoding="utf-8")
        for directive in find_directives(text):
            for problem in validate_directive(directive):
                errors.append(f"{path}: {problem}")
    return errors


def make_badge_html(notebook_rel_path: str, github_repo: str) -> str:
    """
    Return raw HTML string containing Colab and Kaggle badge links.

    notebook_rel_path: path relative to repo root, e.g.
        'notebooks/W1D2_InteractiveContent/W1D2_Tutorial1.ipynb'
    github_repo: 'org/repo' string, e.g. 'neuromatch/course-template'
    """
    colab_url = (
        f"https://colab.research.google.com/github/{github_repo}"
        f"/blob/{NOTEBOOKS_BRANCH}/{notebook_rel_path}"
    )
    kaggle_url = (
        f"https://kaggle.com/kernels/welcome?src="
        f"https://raw.githubusercontent.com/{github_repo}/{NOTEBOOKS_BRANCH}/{notebook_rel_path}"
    )

    return (
        f'<a href="{colab_url}" target="_blank">'
        f'<img src="https://colab.research.google.com/assets/colab-badge.svg" '
        f'alt="Open In Colab"/></a> '
        f'<a href="{kaggle_url}" target="_blank">'
        f'<img src="https://kaggle.com/static/images/open-in-kaggle.svg" '
        f'alt="Open In Kaggle"/></a>'
    )


def inject_badges_into_md(
    md_file: Path, notebook_rel_path: str, github_repo: str, dry_run: bool
) -> None:
    """
    Insert Colab/Kaggle badge HTML into the .md source after the frontmatter block.

    Idempotent: removes any existing badge block before inserting.
    This makes badges appear on the rendered MyST book page.
    """
    badge_html = make_badge_html(notebook_rel_path, github_repo)

    print(f"  Injecting badges into MD: {md_file}")
    if dry_run:
        return

    content = md_file.read_text(encoding="utf-8")

    # Split off frontmatter: content starts with ---, find closing ---
    if not content.startswith("---"):
        return  # no frontmatter, skip

    fm_end = content.find("---", 3)
    if fm_end == -1:
        return

    frontmatter = content[: fm_end + 3]  # includes closing ---
    body = content[fm_end + 3:]           # everything after closing ---

    # Remove an existing badge line (idempotency). Anchored to the start of the
    # body and restricted to a single line so badge HTML used as an example
    # elsewhere on the page (e.g. inside a code block) is never touched.
    body = re.sub(
        r"\A\s*<a href=\"https://colab\.research\.google\.com/[^\n]*?</a>[ \t]*"
        r"<a href=\"https://kaggle\.com/[^\n]*?</a>[ \t]*\n",
        "",
        body,
    )

    # Normalise spacing so repeated runs don't accumulate blank lines
    new_content = f"{frontmatter}\n{badge_html}\n\n{body.lstrip(chr(10))}"
    md_file.write_text(new_content, encoding="utf-8")


def make_badge_cell(notebook_rel_path: str, github_repo: str) -> dict:
    """
    Return a Jupyter markdown cell containing Colab and Kaggle badge links.

    notebook_rel_path: path relative to repo root, forward-slash separated,
        e.g. 'notebooks/W1D2_InteractiveContent/W1D2_Tutorial1.ipynb'
    github_repo: 'org/repo' string, e.g. 'neuromatch/course-template'
    """
    return {
        "cell_type": "markdown",
        "id": "badges",
        "metadata": {},
        "source": [make_badge_html(notebook_rel_path, github_repo)],
    }


def convert_md_to_notebook(md_file: Path, out_path: Path, dry_run: bool) -> None:
    """Convert a MyST .md file to .ipynb using jupytext."""
    print(f"  Converting: {md_file} -> {out_path}")
    if dry_run:
        return

    out_path.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [
            sys.executable, "-m", "jupytext",
            "--from", "md:myst",
            "--to", "notebook",
            "--output", str(out_path),
            str(md_file),
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"  ERROR: jupytext failed for {md_file}", file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        sys.exit(1)


def expand_media(notebook_path: Path, dry_run: bool) -> None:
    """Replace {nma-video}/{nma-slides} directives with NMA code cells."""
    if dry_run:
        return
    with notebook_path.open(encoding="utf-8") as fh:
        nb = json.load(fh)
    count = expand_notebook(nb)
    if count:
        print(f"  Expanded {count} video/slides directive(s): {notebook_path}")
        with notebook_path.open("w", encoding="utf-8") as fh:
            json.dump(nb, fh, indent=1, ensure_ascii=False)


def inject_badges(notebook_path: Path, github_repo: str, dry_run: bool) -> None:
    """Insert Colab/Kaggle badge cell at position 0. Idempotent."""
    notebook_rel = str(notebook_path).replace("\\", "/")
    badge_cell = make_badge_cell(notebook_rel, github_repo)

    print(f"  Injecting badges: {notebook_path}")
    if dry_run:
        return

    with notebook_path.open(encoding="utf-8") as fh:
        nb = json.load(fh)

    # Remove any existing badge cell (idempotency — safe to re-run)
    nb["cells"] = [
        c for c in nb["cells"]
        if "colab-badge.svg" not in "".join(c.get("source", []))
    ]

    nb["cells"].insert(0, badge_cell)

    with notebook_path.open("w", encoding="utf-8") as fh:
        json.dump(nb, fh, indent=1, ensure_ascii=False)


def process_tutorials(github_repo: str, dry_run: bool, md_badges_only: bool) -> int:
    """Walk tutorials/ and process all executable .md pages. Returns count processed."""
    count = 0

    for source_file in sorted(TUTORIALS_DIR.rglob("*.md")):
        if not has_kernelspec(source_file):
            continue  # static page — skip

        # Determine output path under notebooks/
        relative_to_tutorials = source_file.relative_to(TUTORIALS_DIR)
        out_path = NOTEBOOKS_DIR / relative_to_tutorials.with_suffix(".ipynb")

        if md_badges_only:
            notebook_rel = str(out_path).replace("\\", "/")
            inject_badges_into_md(source_file, notebook_rel, github_repo, dry_run)
        else:
            convert_md_to_notebook(source_file, out_path, dry_run)
            expand_media(out_path, dry_run)
            inject_badges(out_path, github_repo, dry_run)

        count += 1

    return count


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert MyST tutorials to Jupyter notebooks with Colab/Kaggle badges"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be done without writing any files",
    )
    parser.add_argument(
        "--inject-md-badges",
        action="store_true",
        help=(
            "Only inject Colab/Kaggle badge HTML into the .md sources (in place). "
            "Intended for CI right before `myst build`; do not commit the result."
        ),
    )
    args = parser.parse_args()

    errors = validate_content()
    if errors:
        print("Content rule violations:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        sys.exit(1)

    if args.dry_run:
        print("DRY RUN — no files will be written\n")

    github_repo = load_github_repo(MYST_CONFIG)
    print(f"GitHub repo: {github_repo}\n")

    count = process_tutorials(github_repo, args.dry_run, args.inject_md_badges)
    print(f"\nDone. Processed {count} file(s).")


if __name__ == "__main__":
    main()
