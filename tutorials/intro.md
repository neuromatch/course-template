---
title: Welcome to the Neuromatch Course Template
jupyter: false
---

A working example of a Neuromatch course and a guide for course authors.
Every page demonstrates a real authoring pattern — the content explains the pattern
while the page itself demonstrates it.

## How to use this template

1. **Fork** this repository on GitHub
2. **Update** `myst.yml` with your course title, authors, and GitHub URL
3. **Replace** the tutorial content with your course material, keeping the file structure
4. **Push** to `main` — GitHub Actions builds and publishes automatically

## What you will learn in this template

| Day | Topic |
|-----|-------|
| [Day 1: Getting Started](W1D1_GettingStarted/chapter_intro.md) | Writing course content in MyST Markdown |
| [Day 2: Interactive Content](W1D2_InteractiveContent/chapter_intro.md) | Adding interactive and rich outputs |
| [Day 3: Publishing and CI](W1D3_PublishingAndCI/chapter_intro.md) | Publishing to GitHub Pages with CI |

## Why MyST instead of Jupyter notebooks?

MyST `.md` files are the **source of truth** for your course content. Jupyter notebooks (`.ipynb`)
are generated automatically by CI for students who want to run code in Colab or Kaggle — you never
edit them by hand.

Benefits:
- **Clean git history** — no output noise or cell metadata cluttering your diffs
- **Human-readable** — readable in any text editor, easy to review
- **In-browser execution** — students can run code directly in this book via JupyterLite, no install needed
- **Colab and Kaggle badges** — auto-injected by CI on every executable tutorial

## Prerequisites for course authors

- A GitHub account with Pages enabled
- Basic familiarity with Markdown
- Python 3.10+ (for local preview)
- See [Day 3, Tutorial 1](W1D3_PublishingAndCI/W1D3_Tutorial1.md) for the full GitHub Actions setup guide.

## Licensing

When you fork this template, update these licenses to match your institution's requirements.
Content is licensed [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/).
Code is licensed [BSD-3-Clause](https://opensource.org/licenses/BSD-3-Clause).
