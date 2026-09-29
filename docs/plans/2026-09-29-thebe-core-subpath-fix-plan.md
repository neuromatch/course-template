# thebe-core publicPath Subpath Fix Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix JupyterLite/Thebe cell activation on GitHub Pages by patching thebe-core's hardcoded webpack publicPath in CI.

**Architecture:** Add a single post-build step in the publish-book CI workflow that patches `__webpack_require__.p="/"` to include the repo subpath. Also file an upstream issue on jupyter-book/thebe.

**Tech Stack:** GitHub Actions, sed, bash

---

### Task 1: Patch publish-book.yml

**Files:**
- Modify: `.github/workflows/publish-book.yml:44-48` (add step after "Build MyST book")

**Step 1: Add the patch step**

In `.github/workflows/publish-book.yml`, add a new step between "Build MyST book" and "Upload pages artifact" (between lines 48 and 49):

```yaml
      - name: Fix thebe-core publicPath for subpath deployment
        # Workaround: thebe-core.min.js hardcodes __webpack_require__.p="/"
        # which breaks chunk loading on GitHub Pages subpath deployments.
        # thebe-lite.min.js uses publicPath:"auto" and works correctly.
        # Remove this step once upstream fix ships:
        # https://github.com/jupyter-book/thebe/issues/XXXX
        run: |
          THEBE_FILE="_build/html/thebe-core.min.js"
          if [ -f "$THEBE_FILE" ]; then
            sed -i 's|__webpack_require__\.p="/"|__webpack_require__.p="/'"$REPO_NAME"'/"|' "$THEBE_FILE"
            echo "Patched thebe-core.min.js publicPath to /$REPO_NAME/"
          else
            echo "Warning: thebe-core.min.js not found, skipping patch"
          fi
        env:
          REPO_NAME: ${{ github.event.repository.name }}
```

**Step 2: Verify the workflow YAML is valid**

Run: `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/publish-book.yml'))"`
Expected: No output (valid YAML)

**Step 3: Commit**

```bash
git add .github/workflows/publish-book.yml
git commit -m "fix: patch thebe-core publicPath for GitHub Pages subpath deployment"
```

### Task 2: Verify locally that the sed pattern matches

**Step 1: Test the sed command against the local build**

Run:
```bash
grep -c '__webpack_require__\.p="/"' _build/html/thebe-core.min.js
```
Expected: `1` (exactly one match)

**Step 2: Test the replacement**

Run:
```bash
cp _build/html/thebe-core.min.js /tmp/thebe-core-test.min.js
sed -i 's|__webpack_require__\.p="/"|__webpack_require__.p="/course-template/"|' /tmp/thebe-core-test.min.js
grep -o '__webpack_require__\.p="[^"]*"' /tmp/thebe-core-test.min.js
```
Expected: `__webpack_require__.p="/course-template/"`

### Task 3: Push and verify deployment

**Step 1: Push to main**

```bash
git push origin main
```

**Step 2: Monitor the CI workflow**

Check GitHub Actions for the "Publish Book" workflow. Verify the "Fix thebe-core publicPath" step runs successfully and logs `Patched thebe-core.min.js publicPath to /course-template/`.

**Step 3: Test on deployed site**

1. Open `https://neuromatch.github.io/course-template/tutorials/w1d1-getting-started/w1d1-tutorial1/`
2. Click the JupyterLite power button (top right)
3. Wait ~10 seconds for kernel initialization
4. Confirm code cells become editable (CodeMirror editors appear)
5. Open browser DevTools > Network tab, filter for `thebe-core` -- confirm no 404s
6. Navigate to the W2D1_Tutorial1 page and verify exercise cells are also editable

### Task 4: File upstream issue (manual)

File an issue on `https://github.com/jupyter-book/thebe` with:

**Title:** `thebe-core webpack publicPath is hardcoded to "/" -- breaks subpath deployments`

**Body:**
- `thebe-core.min.js` uses `__webpack_require__.p="/"` (hardcoded)
- `thebe-lite.min.js` uses automatic publicPath detection (correct)
- On subpath deployments (GitHub Pages), thebe-core chunk requests 404
- Suggested fix: change thebe-core's webpack config to `publicPath: "auto"`

Update the comment in `publish-book.yml` with the actual issue URL once filed.
