---
title: Welcome to the Neuromatch Course Guide
---

A guide for course authors and a working example of a Neuromatch course.
Every page demonstrates a real authoring pattern — the content explains the pattern
while the page itself demonstrates it.

## How to use this guide

Don't fork or copy this repository: your course won't merge back into it, and its
content will diverge. Read the guide, and start your own course from a fresh
repository:

1. **Generate** a starter with `nma-kit init` (see [Starting a new course](new_course.md))
2. **Replace** the example day with your course material
3. **Push** to `main`. GitHub Actions builds and publishes automatically
4. **Come back here** for any feature: each day below is a reference for one area

## What you will learn in this guide

| Day | Topic |
|-----|-------|
| [Day 1: Getting Started](W1D1_GettingStarted/chapter_intro.md) | Writing course content in MyST Markdown |
| [Day 2: Interactive Content](W1D2_InteractiveContent/chapter_intro.md) | Adding interactive and rich outputs |
| [Day 3: Publishing and CI](W1D3_PublishingAndCI/chapter_intro.md) | Publishing to GitHub Pages with CI |
| [Week 2 Day 1: Examples](W2D1_Examples/chapter_intro.md) | A real tutorial as a normal page and a scrolly page |

## Why MyST instead of Jupyter notebooks?

MyST `.md` files are the **source of truth** for your course content. Jupyter notebooks (`.ipynb`)
are generated automatically by CI for students who want to run code in Colab or Kaggle — you never
edit them by hand.

Benefits:
- **Clean git history** — no output noise or cell metadata cluttering your diffs
- **Human-readable** — readable in any text editor, easy to review
- **In-browser execution** — students can edit and run code cells directly in this book (JupyterLite), no install needed
- **Colab and Kaggle badges** — auto-injected by CI on every executable tutorial

## Prerequisites for course authors

- A GitHub account with Pages enabled
- [uv](https://docs.astral.sh/uv/) and Node.js >= 20
- Basic familiarity with Markdown
- Python 3.10+ (for local preview)
- See [Day 3, Tutorial 1](W1D3_PublishingAndCI/W1D3_Tutorial1.md) for the full GitHub Actions setup guide.

## Licensing

`nma-kit init --license` writes the licence you choose into your course, so set it to match
your institution's requirements. This guide's own content is licensed [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/),
and its code is licensed [BSD-3-Clause](https://opensource.org/licenses/BSD-3-Clause).
