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

## Branding

The kit provides the Neuromatch look: colours, the Rubik font, logos, favicon,
and the styling of its own widgets. `nma-kit sync-assets` writes them to `_nma/`
(CI does this automatically; run it once locally before `myst start`, and again
after upgrading the kit). `myst.yml` points at those files:

```yaml
site:
  options:
    logo_text: Your Course Title   # your course's name next to the logo
    style: _nma/site.css
    logo: _nma/logo.svg
    logo_dark: _nma/logo-dark.svg
    favicon: _nma/favicon.png
```

## Changing the colours

Set any of these in the `nma:` block of `myst.yml` (all optional, `"#RRGGBB"`):

```yaml
nma:
  brand:
    primary: "#D9480F"       # links, accents, buttons
    primary_hover: "#A63700" # default: primary, 25% darker
    primary_light: "#FF8A57" # accent on dark backgrounds
    secondary: "#45429C"     # header surface, tips
    accent: "#FA7A7A"        # exercise cells
```

## Using your own logo

To replace the Neuromatch logo, place your file in `_static/` and point the
logo options at it instead of `_nma/`:

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
icon rather than a full wordmark. See Tutorial 2 of Week 1 Day 1 for the same options in the
context of the sidebar and table of contents.

## Custom CSS

Put your own rules in a file such as `_static/extra.css` and list it in `myst.yml`.
The kit appends it after its own stylesheet (into `_nma/site.css`), so your
rules win. The brand colours are CSS variables (`--nma-brand-primary`, ...):

```yaml
nma:
  style:
    extra: _static/extra.css
```

Example contents:

```css
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
