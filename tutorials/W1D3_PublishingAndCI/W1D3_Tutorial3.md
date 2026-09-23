---
title: "Tutorial 3: Customising Your Book"
---

# Tutorial 3: Customising Your Book

## Changing the title and metadata

Edit `myst.yml` — these fields appear in the browser tab, sidebar, and Open Graph
metadata when the book is published:

```yaml
project:
  title: Computational Neuroscience 2027
  description: An introduction to modelling the brain
  authors:
    - name: Your Name
      github: your-github-username
  github: https://github.com/your-org/your-course-repo
```

## Adding a logo

Place your logo file in `_static/` and reference it in `myst.yml`:

```yaml
site:
  options:
    logo: _static/your_logo.png
```

SVG and PNG both work. The logo appears in the top-left of the sidebar.

## Custom CSS

Edit `_static/custom.css` — it is already wired into the book via `myst.yml`.
Use it to override colours, fonts, or spacing:

```css
/* Change the primary colour */
:root {
  --color-primary: #FF6B6B;
}

/* Style exercise admonitions */
.admonition.tip {
  border-left-color: #4ECDC4;
}
```

## Adding a Binder badge

Show a persistent Binder launch badge on every page:

```yaml
project:
  binder: https://mybinder.org/v2/gh/your-org/your-repo/HEAD
```

## Enabling download buttons

Let students download pages as PDF or Jupyter notebook:

```yaml
site:
  options:
    downloads: true
```

## Choosing a different theme

MyST uses `book-theme` by default. To list available themes:

```bash
myst templates list --site
```

Then set it in `myst.yml`:

```yaml
site:
  template: book-theme
```
