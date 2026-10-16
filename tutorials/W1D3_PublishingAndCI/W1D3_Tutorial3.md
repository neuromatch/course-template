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
    logo: _static/your_logo.svg
    logo_dark: _static/your_logo_dark.svg   # optional, shown in dark mode
    logo_text: Your Course Title             # optional, shown next to the logo
```

SVG and PNG both work. The logo appears in the top-left of the sidebar.
`logo_dark` swaps in a light version of the logo when the reader is in dark mode,
and `logo_text` puts the course title beside the logo — handy when the logo is an
icon rather than a full wordmark. See Tutorial 2 for the same options in the
context of the sidebar and table of contents.

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
