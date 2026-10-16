# Course kit: extracting the CI and MyST extensions from the template

Date: 2026-10-16
Status: draft, awaiting approval

## Intent

Today every Neuromatch course is a fork of `course-template`, and each fork
carries its own copy of the tooling: `plugins/` (MyST plugins), `scripts/`
(notebook conversion and checks), `tests/`, and `.github/workflows/`. A fix
to that tooling has to be copied into every course by hand, and copies drift.

We want the tooling to live in **one separately versioned project, the course
kit**. The template and every course *use* a version of the kit; they don't
contain it. A kit fix ships once. Courses that want live updates get it on
their next build, and courses that want to freeze (a finished course) pin a
version.

The template becomes the kit's first user: content, `myst.yml`, branding,
`_static/`, and a ~15-line workflow file.

## Goals

- One repo, `neuromatch/course-kit`, holds the MyST plugin, the Python
  CLI, the reusable GitHub workflows, their tests and the shared fixtures.
- **One version number covers everything.** The JS plugin and Python CLI
  implement twin rules (URL templates, `cell_key`, `# @param` grammar,
  `runtime_of`, the fallback marker). They are released together and a build
  always uses a matching pair, so the twins can never be mixed across
  versions.
- A course chooses its update policy with **one knob**, the ref in its
  workflow file (see "Versioning and live updates").
- Fix the CI problems found in the audit (below).
- The output is unchanged: generated notebooks, solution files and the
  rendered site are the same before and after the move (verified by a golden
  comparison, see "Acceptance").
- Delivered first as a folder, `course-kit/`, inside this repo that can be
  lifted out to its own repo as-is (see "Delivery in two phases").

## Non-goals

- No new authoring features, directives or frontmatter keys.
- Not merging the Python/JS twins into one implementation. They stay
  twins, tested against the same fixtures, now in the same repo.
- Not changing where notebooks are published (`notebooks-branch`) or how
  students open them (Colab/Kaggle badges).
- No Binder/JupyterHub/remote kernels (unchanged).

## Anti-goals (failure even if it "works")

- A course needs Node, `npm install`, or a `package.json` to build.
- A course has to edit more than its one workflow file to pick up a kit
  release.
- A plugin from one version runs against a CLI from another.
- Course CI fails because of a kit-internal check the author can't act on
  (bundle staleness, kit unit tests, flaky CDN browser tests).
- A new fork's first push fails.

## Audit findings this design fixes

| # | Finding | Fix |
|---|---|---|
| 1 | No CI on pull requests; validation only runs after merge, inside the job that pushes notebooks | `course-check` reusable workflow on `pull_request` and `push` |
| 2 | `publish-book` runs on `workflow_run` of `generate-notebooks` without checking it succeeded; a push touching `tutorials/` and `myst.yml`/`scripts/` deploys twice | One `course-publish` workflow, one job chain: check, notebooks, site, deploy |
| 3 | Fresh fork: `git worktree add … notebooks-branch` fails when the branch doesn't exist | CLI/workflow creates an orphan `notebooks-branch` if missing |
| 3b | `CNAME` (`template.neuromatch.io`) is copied into every fork's deploy | Drop the CNAME step: with Pages "GitHub Actions" source the custom domain is a repo setting and a `CNAME` file in the artifact isn't used (builder: confirm in GitHub docs) |
| 4 | Every course runs template-internal checks: pytest of `scripts/`, JS unit tests, bundle staleness, Playwright against CDNs | These move to the kit's own CI; courses run only content checks and the build |
| 5 | No caching; concurrent notebook pushes can race; only `mystmd` pinned | `setup-uv`/`setup-node` caching, `concurrency` group on the notebooks push, kit pins its own toolchain (mystmd, jupytext, nbclient) |
| 5b | `build-pyodide-wheels.yml` uploads to GitHub Releases, which AGENTS.md says aren't CORS-friendly; `_wheels/` is empty | Kit ships a reusable wheels workflow that commits wheels to the course's `_wheels/` (served via `raw.githubusercontent.com`) |
| 6 | Plugins import each other by relative path (`../nma.mjs`), reference assets by root-absolute paths (`/plugins/cells/cells.css`), and are coupled to the template's layout | Plugins become one bundled `.mjs`; assets referenced by versioned URL (see "MyST plugin") |
| 7 | Hard-coded conventions: `tutorials/`, `notebooks-branch` (3 places), `W1D1_Tutorial1` naming | Optional `nma:` settings with today's values as defaults |
| 8 | Hand-written YAML reader in JS (`readNmaConfig`) exists only because plugins were unbundled | Bundled plugin can use a real YAML parser (see "Config") |
| 9 | `scripts/` isn't a package (tests use a `sys.path` hack); 380 KB bundle committed in `plugins/cells/dist/` | Proper Python package; bundles built in kit CI and published, not committed in courses |

## What MyST 1.11 supports (verified in the bundled `myst.cjs`)

- `project.plugins` entries may be **URLs** (`allowRemote` for non-executable
  plugins). MyST downloads one file and caches it. So the plugin must be a
  single bundled `.mjs`.
- `extend:` in `myst.yml` accepts **URLs**, so shared config can be pulled
  in.
- `anywidget` `esm`/`css` may be **URLs**. MyST downloads them at build time
  and serves them from the site (`transformWidgetStaticAssetsToDisk`), so
  readers' browsers don't fetch them from the CDN.
- Remote config/plugin files are cached in `_build/cache` for **30 days**
  (`maxAge: 30`, in days). That doesn't matter on CI (fresh checkout) but does
  for local previews (`myst clean --cache` refreshes).

## Architecture

```
neuromatch/course-kit          (one repo, one version, tags vX.Y.Z + floating v0.MINOR/vMAJOR)
├── js/        → npm  @neuromatch/course-kit      (bundled MyST plugin + widget assets + nma.yml)
├── python/    → PyPI neuromatch-course-kit        (CLI `nma-kit`, pins mystmd/jupytext/nbclient)
└── .github/workflows/course-*.yml                 (reusable workflows, `workflow_call`)

course repo (template or a real course)
├── myst.yml           extend: <kit nma.yml URL>   + course settings, toc, nma: block
├── requirements.txt   content deps only (numpy, matplotlib, …)
├── .github/workflows/course.yml   → uses: neuromatch/course-kit/.github/workflows/course-publish.yml@v0.1
└── tutorials/, _static/, _wheels/, projects/
```

### MyST plugin (`js/`)

- **Organised as separate plugins, shipped as one bundle** (user decision).
  Each feature is its own folder with its own MyST plugin object, browser
  assets and tests; today's `nma.mjs`, which mixes three features, is split:

  ```
  js/src/
    shared/      config.mjs (readNmaConfig, settings), paths.mjs (githubRepo,
                 pageLocation, notebookUrls), assets.mjs (assetUrl)
    media/       plugin.mjs ({nma-video}, {nma-slides})
    solutions/   plugin.mjs ({nma-solution}, {nma-explanation}, link transform)
    feedback/    plugin.mjs ({nma-feedback} + transform), assets/widget.mjs
    scrolly/     plugin.mjs ({step}, {stage}, transform), assets/{engine,runnable}.mjs, *.css
    cells/       plugin.mjs (transform), src/ (CodeMirror panel, runtime), assets/*.css
    index.mjs    imports every plugin and merges directives and transforms
  ```

  Plugins depend only on `shared/`, never on each other (today `cells`
  imports from `nma.mjs` and `scrolly.mjs`; those helpers move to
  `shared/`). `index.mjs` keeps today's transform order: media, solutions,
  feedback, then scrolly, then cells.
- esbuild bundles `index.mjs` to one `dist/nma.mjs` (Node target, `node:`
  builtins external), because MyST loads a remote plugin as a single file.
  Courses list one plugin. Per-plugin bundles (so a course could load only
  some) are possible later from the same sources but are not built now.
- Browser assets (feedback widget, scrolly engine/runnable, cells
  panel/runtime-widget, all CSS) are built into `dist/assets/<plugin>/` and
  published in the same npm package. The Python side mirrors the same
  feature names (`nma_kit.media`, `.solutions`, `.feedback`, `.scrolly`,
  `.cells`).
- **Asset URLs are baked at build time** via an esbuild `define`
  (`__NMA_ASSET_BASE__`):
  - release build: `https://cdn.jsdelivr.net/npm/@neuromatch/course-kit@<exact version>/dist/assets/`.
    An exact version is cached forever by jsDelivr, so the plugin and its
    assets always match.
  - dev build (`npm run build:dev`): a project-root-relative path to the
    local `dist/assets/` (today's `/plugins/...` style). This only works when
    the kit folder is inside the course directory, which is true in phase 1
    and for kit development against `example-course/`.
- `dist/nma.yml` is generated per release and is the file courses `extend:`:

  ```yaml
  version: 1
  project:
    jupyter:
      lite: true
    plugins:
      - https://cdn.jsdelivr.net/npm/@neuromatch/course-kit@0.1.3/dist/nma.mjs
  ```

  Keep it to what the kit needs (`jupyter.lite: true` is required for the
  editable cells). Theme and branding stay in the course.

### Python CLI (`python/`)

Package `neuromatch-course-kit`, module `nma_kit`, console script `nma-kit`.
Today's `scripts/*.py` move in mostly unchanged (`nma_media` → `nma_kit.media`,
etc.), and the `sys.path` hack goes away.

| Command | Replaces |
|---|---|
| `nma-kit check` | the validation done at the start of `convert_to_notebooks.py` (both modes) |
| `nma-kit notebooks [--dry-run]` | `convert_to_notebooks.py` default mode |
| `nma-kit render-scrolly` | `nma_scrolly.py --render` |
| `nma-kit prepare-site` | `convert_to_notebooks.py --prepare-site`, **plus** rewriting the course's `extend:` kit URL to the CLI's own exact version (see "Versioning") |
| `nma-kit publish-notebooks` | the shell in `generate-notebooks.yml` (worktree, rsync, commit, push), creating `notebooks-branch` as an orphan if it doesn't exist |

Dependencies: the kit pins `mystmd==1.11.0` (the cells use mystmd's bundled
thebe 0.5.0 API), plus jupytext, nbclient, nbformat, ipykernel, pyyaml. CI
installs the kit **into the same venv as the course's `requirements.txt`**,
because `render-scrolly` executes tutorial code and needs the course's
packages.

### Config

- The `nma:` block in the course's `myst.yml` stays the single place for kit
  settings. New optional keys with today's values as defaults:
  `nma.paths.tutorials` (`tutorials`), `nma.notebooks.branch`
  (`notebooks-branch`). The filename → feedback-prefix rule stays as it is
  (`feedback_prefix:` frontmatter already overrides it).
- Both sides read the course's own `myst.yml` from the working directory, as
  today. The `nma:` block is never in the extended kit file.
- Replace the JS line-based reader with a real YAML parser (`yaml` npm
  package, bundled) and the Python one with `yaml.safe_load`. **Builder's
  call:** keep rejecting non-string values for now, so existing `nma:` blocks
  behave the same. The shared `fixtures/nma_config/` cases still have to pass
  on both sides.

### Reusable workflows

In `course-kit/.github/workflows/`:

- **`course-check.yml`**: install, `nma-kit check`, `nma-kit notebooks
  --dry-run`, `myst build --html` (no deploy). For PRs.
- **`course-publish.yml`**: one job chain, all steps gated on the previous one:
  1. check
  2. `nma-kit notebooks` and `nma-kit publish-notebooks` (in a `concurrency:
     notebooks-${{ github.repository }}` group)
  3. `nma-kit render-scrolly`, `nma-kit prepare-site`, `myst build --html`
  4. upload the Pages artifact and deploy

  Notebooks are pushed before the site deploys, so solution links resolve
  when the site goes live.
- **`course-wheels.yml`**: `workflow_dispatch` caller input `packages`. Builds
  pure-Python wheels and commits them to the course's `_wheels/`.
- Inputs (all optional): `python-version`, `requirements` (default
  `requirements.txt`), `kit-version` (override, see below),
  `working-directory`.
- `uv` and Node caching enabled. Node is only needed because mystmd needs
  it; courses never run npm.

What a course commits (`.github/workflows/course.yml`):

```yaml
name: Course
on:
  push: { branches: [main] }
  pull_request:
  workflow_dispatch:
jobs:
  check:
    if: github.event_name == 'pull_request'
    uses: neuromatch/course-kit/.github/workflows/course-check.yml@v0.1
  publish:
    if: github.event_name != 'pull_request'
    uses: neuromatch/course-kit/.github/workflows/course-publish.yml@v0.1
    permissions: { contents: write, pages: write, id-token: write }
```

### Kit's own CI (`course-kit/.github/workflows/ci.yml`, `release.yml`)

- `ci.yml` (PRs and main): pytest, `node --test`, bundle build, then a
  build of `example-course/` with the dev bundle and the Playwright smoke
  test against it. This is where the template's `tests/e2e` goes. It needs
  its own minimal pages, copied from the template pages the e2e test uses
  today (W2D1 Tutorial1/Tutorial3, W1D1 Tutorial1).
- It also runs the reusable workflows against `example-course/`
  (`uses: ./.github/workflows/course-check.yml`) so they're tested before
  release.
- `release.yml`: release-please (builder's call) opens a release PR that
  bumps the one version in `package.json`, `pyproject.toml` and the default
  `KIT_VERSION` inside the reusable workflows. Merging it tags `vX.Y.Z`,
  publishes to npm and PyPI (trusted publishing, no long-lived tokens), and
  moves the floating tags (see "Versioning").

## Versioning and live updates

**The single knob is the ref in the course's workflow file.** Each tagged
commit of the reusable workflow contains `KIT_VERSION: X.Y.Z` (stamped at
release). The workflow installs that exact CLI version, and `nma-kit
prepare-site` rewrites the course's `extend:` URL to the same exact version
before `myst build`, in CI's throwaway checkout, just as it already adds
badges. So the CLI, the plugin and the assets always come from one release.

**Start at 0.1.0 (user decision)** and stay on 0.x until the kit is stable.
Semver treats every 0.x minor as potentially breaking, so release-please is
configured with `bump-minor-pre-major: true` (a breaking change bumps
0.1.x → 0.2.0) and `bump-patch-for-minor-pre-major: true` (features and
fixes bump the patch). A 0.MINOR line is therefore the compatible line, and
the release workflow moves a floating **`v0.MINOR`** tag (e.g. `v0.1`) as
well as `v0`. From 1.0.0 on, the floating tag that matters is `vMAJOR`.

| Course wants | Workflow ref (0.x) | After 1.0 | What happens |
|---|---|---|---|
| Live updates, safe (recommended, template default) | `@v0.1` | `@v1` | Every build uses the newest release of that compatible line. Breaking changes ship as 0.2 (or v2) and need an opt-in |
| Live updates including breaking changes | `@v0` | (not offered) | Newest 0.x, whatever it is. Only for courses tracking the kit closely |
| Bleeding edge (kit maintainers) | `@main` | `@main` | Uses the kit's `main`. Builder: `main` installs the CLI from git at that commit, and `prepare-site` points `extend:` at a dev build |
| Frozen (a finished course) | `@v0.1.3` or a commit SHA | `@v1.4.2` | Never changes. Dependabot (`github-actions` ecosystem) can propose bumps |

**About "latest":**
- GitHub Actions has no automatic `latest` ref, so the floating tags above
  are "latest within a line".
- npm/jsDelivr do have `@latest`, but jsDelivr caches alias URLs (`@0.1`,
  `@latest`) for **7 days**, and purging needs API access granted by email.
  `@latest` also crosses major versions.

The design therefore never depends on alias URLs at build time. Courses
should not put `@latest` in `myst.yml`. The `extend:` URL committed in
`myst.yml` (`…@0.1/dist/nma.yml`) is only used by local previews and is
replaced with an exact version on CI. The workflow also accepts
`kit-version: latest` as an explicit override, which resolves the newest
version on PyPI at build time.

## Delivery in two phases

**Phase 1, in this repo (sandbox).** Build `course-kit/` at the repo root,
laid out exactly like the future repo:

```
course-kit/
  README.md  AGENTS.md  CHANGELOG.md  LICENSE
  js/        package.json, src/ (plugins + browser code), build script, dist/ (gitignored)
  python/    pyproject.toml, src/nma_kit/
  fixtures/  shared Python/JS fixtures (moved from tests/fixtures/)
  tests/     python/, js/, e2e/
  example-course/   minimal course for kit CI and e2e
  .github/workflows/ ci.yml, release.yml, course-check.yml, course-publish.yml, course-wheels.yml
  templates/course.yml   the caller workflow courses copy
```

- Nested `.github/` is inert inside the template, which is fine.
- The template switches to the in-repo kit so the move is proven end to end
  before extraction:
  - `myst.yml` plugins → `course-kit/js/dist/nma.mjs` (dev build)
  - the template's workflow installs `./course-kit/python` and runs `nma-kit …`
  - `plugins/`, `scripts/`, `tests/` and the old workflows are deleted from
    the template
- Template AGENTS.md keeps the authoring conventions. The plugin and script
  internals move to `course-kit/AGENTS.md`.
- Update the tutorials that describe the internals: W1D1 T4, W1D2 T4, W1D2
  T6, W1D3 T1/T2. W1D3 T1 `literalinclude`s the workflows and will now show
  the caller.
- Extraction: `git subtree split --prefix=course-kit -b course-kit-export`
  (keeps history), push to `neuromatch/course-kit`. Or just copy the
  folder.

**Phase 2, after extraction and the first release (v0.1.0).** The template's
`myst.yml` uses `extend:` with the kit URL. Its workflow becomes
`templates/course.yml` at `@v0.1`. `course-kit/` is deleted from the template.

## Spike first (before the bulk of phase 1)

Prove these with a throwaway build. Each one, if it fails, changes the
design:

1. A plugin URL listed inside a **remote** `extend:` file resolves and loads
   (the extended file sits in `_build/cache`). Fallback: list the plugin URL
   directly in the course's `myst.yml`.
2. anywidget assets given as remote URLs get downloaded and served for
   `esm` **and** `css`.
3. The editable-cells bundle finds thebe: `thebeScriptUrls` resolves
   `../thebe-core.min.js` from `import.meta.url`, which must still point at
   the site's `build/` folder after MyST rehashes the downloaded asset.
4. `page.css`/`scrolly.css`, which are copied into `<head>`, still work when
   served from the hashed name.
5. With the Pages Actions source, the custom domain survives without a
   `CNAME` file in the artifact.

## Acceptance

- **Golden comparison:** build the template on `main` and on the phase-1
  branch.
  - Generated `notebooks/` (student, instructor, solutions) are identical,
    ignoring the badge cell only if URLs legitimately change.
  - Each page's rendered HTML has the same directive output: video tabs,
    solution links, feedback widgets, scrolly stages, cell panels.
- All moved tests pass in `course-kit/`, plus the e2e smoke test against
  `example-course/`.
- A PR to the template runs `course-check`. A failing check blocks deploy.
- One push to `main` produces one deploy.
- A fresh fork with no `notebooks-branch` publishes on its first push.
- After extraction: a kit patch release reaches a course on `@v0.1` with no
  course commit. A course on `@v0.1.0` is unaffected.

## Decided by the user

- Start at version 0.1.0; stay on 0.x until stable.
- Plugins organised separately in the kit, shipped as one bundle.

- One kit, separate from the template, versioned; template and courses use
  it.
- Courses can opt into live updates.
- Deliver as an extractable folder inside this repo first.

## Registry setup (decided: publish from the user's npm/PyPI accounts)

Checked 2026-10-16: npm scope `@neuromatch` does not exist ("Scope not
found"); `@neuromatch/course-kit`, PyPI `neuromatch-course-kit` and `nma-kit`
are all free. One-time steps, done after extraction to `neuromatch/course-kit`:

1. npm: create the free org `neuromatch` from the user's account. Publish
   the first version by hand (`npm publish --access public` in `js/`), because
   npm trusted publishing can only be configured on an existing package. Then
   add a trusted publisher: repo `neuromatch/course-kit`, workflow
   `release.yml`. After that CI publishes without a token.
2. PyPI: add a *pending publisher* for project `neuromatch-course-kit`
   (repo `neuromatch/course-kit`, workflow `release.yml`, environment
   `release`). The first CI release creates the project.
3. Add a second owner/maintainer on both registries.

Trusted publishing is bound to the repo and workflow, not to a personal
account; the user's account owns the packages.

## My calls (please check)

- Names: repo `neuromatch/course-kit`, npm `@neuromatch/course-kit`, PyPI
  `neuromatch-course-kit`, CLI `nma-kit`.
- Distribution via npm + PyPI + jsDelivr (user confirmed they can publish;
  see "Registry setup").
- The template defaults to `@v0.1`. The workflow ref is the only update knob,
  and `prepare-site` pins the plugin URL to the CLI's version on CI.
- Merge the three plugins into one bundle.
- Use a real YAML parser on both sides, but keep rejecting non-string `nma:`
  values for now.
- release-please for releases; trusted publishing.
- Drop the CNAME step (pending spike item 5).
- The wheels workflow commits to `_wheels/` instead of Releases.

## Left to the builder

- Exact module split inside `nma_kit` and `js/src`.
- esbuild config details, and whether the browser assets are minified.
- How `@main` builds point `extend:` at a dev bundle (e.g. jsDelivr
  `/gh/neuromatch/course-kit@<sha>/…` with dist built into a `dist` branch,
  or GitHub Pages of the kit repo).
- Wording of the updated tutorials and READMEs.
