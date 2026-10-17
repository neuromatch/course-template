# Neuromatch Course Template

A course template built with [JupyterBook v2 (MyST)](https://mystmd.org).

**Live book:** https://neuromatch.github.io/course-template/

## For course authors

Fork this repository and follow the instructions in the book itself.
Each day of this template teaches you how to build and publish your course.
For scrollytelling pages (a pinned stage of figures and live Python beside
scrolling text), see W1D2 Tutorial 6, "Scrollytelling Pages".

## After forking

Update these things before adding content:

1. In `myst.yml`: change `project.title`, `project.authors`, and `project.github`
2. In `README.md`: change the **Live book** URL to match your GitHub Pages URL
3. In GitHub: go to **Settings → Pages** and set Source to **GitHub Actions**
   (set your custom domain there too, if you have one; delete the `CNAME` file)

The first push to `main` publishes the site and creates `notebooks-branch`
for the generated notebooks. Pull requests are checked and built, but not
published.

## The course kit

The MyST plugin, the `nma-kit` command (notebooks, checks, site preparation)
and the CI steps come from the **Neuromatch course kit**, in `course-kit/`
(see its [README](course-kit/README.md)). It will move to its own repository,
`neuromatch/course-kit`; courses will then use a published version instead of
a copy, and get kit fixes on their next build.

## Local preview

Requires **Node.js >= 20** (use `nvm use` if you have `.nvmrc` support) and Python 3.10+.

```bash
uv venv
uv pip install -r requirements.txt ./course-kit/python
(cd course-kit/js && npm ci && npm run build:dev)   # the kit's MyST plugin
uv run nma-kit check                                # content rules, as in CI
uv run myst start
```

The book will be available at http://localhost:3000. For scrollytelling pages,
run `uv run nma-kit render-scrolly` first so their panels show real outputs.
