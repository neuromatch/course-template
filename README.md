# Neuromatch Course Template

A course template built with [JupyterBook v2 (MyST)](https://mystmd.org).

**Live book:** https://neuromatch.github.io/course-template/

## For course authors

Fork this repository and follow the instructions in the book itself.
Each day of this template teaches you how to build and publish your course.

## After forking

Update these three things before adding content:

1. In `myst.yml`: change `project.title`, `project.authors`, and `project.github`
2. In `README.md`: change the **Live book** URL to match your GitHub Pages URL
3. In GitHub: go to **Settings → Pages** and set Source to **GitHub Actions**

## Local preview

Requires **Node.js >= 20** (use `nvm use` if you have `.nvmrc` support) and Python 3.10+.

Install dependencies (choose one):

```bash
# with uv (recommended)
uv venv
uv pip install -r requirements.txt

# with pip
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Then start the local preview server:

```bash
uv run myst start
```

The book will be available at http://localhost:3000.
