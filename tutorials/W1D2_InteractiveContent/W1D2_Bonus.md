---
title: "Bonus: Binder and Remote Kernel Options"
---

# Bonus: Binder and Remote Kernel Options

JupyterLite (in-browser WASM) is the default for this template. For compute-heavy
content or packages not supported by WebAssembly, you can switch to a remote kernel.

## Using Binder

Replace JupyterLite with a mybinder.org-backed kernel by updating `myst.yml`:

```yaml
project:
  jupyter:
    binder:
      repo: your-org/your-repo
      ref: main
```

Students click the power button and a Binder session launches (~30–60 seconds
cold start). The environment is built from your repo's `requirements.txt`,
`environment.yml`, or `Dockerfile`.

## Using a custom BinderHub

If your institution runs a private BinderHub:

```yaml
project:
  jupyter:
    binder:
      url: https://binder.myorganisation.com/services/binder/
      repo: your-org/your-repo
      ref: main
```

## Using JupyterHub

Point students directly at a JupyterHub instance:

```yaml
project:
  jupyter:
    server:
      url: https://hub.myuniversity.edu
```

## Mixing strategies per page

Override the project default on individual pages using frontmatter:

```yaml
---
title: "GPU Tutorial"
jupyter:
  binder:
    repo: your-org/gpu-environment-repo
---
```

Or disable in-browser execution entirely on a specific page:

```yaml
---
title: "Static reference page"
jupyter: false
---
```

## Adding a Binder badge

To show a persistent Binder launch badge on every page (separate from the power
button), add to `myst.yml`:

```yaml
project:
  binder: https://mybinder.org/v2/gh/your-org/your-repo/HEAD
```
