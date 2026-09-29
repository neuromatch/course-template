# Design: Fix thebe-core publicPath for GitHub Pages subpath deployments

**Date:** 2026-09-29
**Status:** Approved

## Problem

When the MyST book is deployed to GitHub Pages at `neuromatch.github.io/course-template/`, clicking the JupyterLite power button fails to activate code cells. No cells become editable -- the kernel never initializes.

## Root Cause

`thebe-core.min.js` (bundled with mystmd) has a hardcoded webpack `publicPath`:

```javascript
__webpack_require__.p = "/"
```

When thebe-core lazy-loads its ~110 chunk files, it constructs URLs like `/1001.thebe-core.min.js` instead of `/course-template/1001.thebe-core.min.js`. All chunk requests 404, preventing kernel initialization.

In contrast, `thebe-lite.min.js` uses automatic publicPath detection and works correctly:

```javascript
// thebe-lite: derives path from script URL (correct)
__webpack_require__.p = e  // e is dynamically computed

// thebe-core: hardcoded (broken on subpaths)
__webpack_require__.p = "/"
```

This is an upstream bug in `jupyter-book/thebe`'s webpack build configuration. The fix should be `publicPath: "auto"` in thebe-core's webpack config.

## Solution

### Immediate: CI post-build patch

Add a step in `.github/workflows/publish-book.yml` after `myst build --html` that patches the hardcoded `publicPath` in `thebe-core.min.js` to include the repository subpath.

```yaml
- name: Fix thebe-core publicPath for subpath deployment
  run: |
    THEBE_FILE="_build/html/thebe-core.min.js"
    if [ -f "$THEBE_FILE" ]; then
      sed -i 's|__webpack_require__\.p="/"|__webpack_require__.p="'"/${GITHUB_REPOSITORY##*/}"'/"|' "$THEBE_FILE"
      echo "Patched thebe-core.min.js publicPath to /${GITHUB_REPOSITORY##*/}/"
    else
      echo "Warning: thebe-core.min.js not found, skipping patch"
    fi
```

Key properties:
- Uses `${GITHUB_REPOSITORY##*/}` for fork-friendly subpath derivation
- Silently skips if the file doesn't exist (future-proof)
- Single `sed` replacement of a unique pattern

### Long-term: Upstream fix

File an issue on `jupyter-book/thebe` requesting `publicPath: "auto"` in thebe-core's webpack config. Remove the CI workaround once the fix ships in a mystmd release.

## Verification

After deployment:
1. Open any page with `kernelspec` on the GitHub Pages site
2. Click the JupyterLite power button
3. Confirm cells become editable after ~10 seconds
4. Check browser DevTools Network tab -- no 404s on `*.thebe-core.min.js` chunks

## Scope

- **Changed file:** `.github/workflows/publish-book.yml` (add one step)
- **No source content changes** -- the `.md` files and `myst.yml` are correct
- **No local dev impact** -- `myst start` serves from `/` where the hardcoded path works fine
