---
title: "Tutorial 2: Structuring Your Table of Contents"
---

# Tutorial 2: Structuring Your Table of Contents

The table of contents for your book lives entirely in `myst.yml` under `project.toc`.
There is no auto-generation script — you edit it directly.

## The myst.yml TOC format

The toc is a list of files and sections:

    project:
      toc:
        - file: tutorials/intro.md
        - title: "Day 1: My Topic"
          children:
            - file: tutorials/W1D1_MyTopic/chapter_intro.md
              children:
                - file: tutorials/W1D1_MyTopic/W1D1_Tutorial1.md
                - file: tutorials/W1D1_MyTopic/further_reading.md

## Naming convention

Follow the Neuromatch naming convention for all tutorial files:

    tutorials/
      W{week}D{day}_{TopicName}/
        chapter_intro.md
        W{week}D{day}_Tutorial1.md
        W{week}D{day}_Tutorial2.md
        W{week}D{day}_Tutorial3.md
        W{week}D{day}_Bonus.md
        further_reading.md

For example: `tutorials/W2D3_ReinforcementLearning/W2D3_Tutorial1.md`

## Adding a new day

1. Create the folder: `tutorials/W2D1_MyNewTopic/`
2. Create the files following the naming convention above
3. Add an entry to `project.toc` in `myst.yml`
4. Push to `main` — CI handles the rest

## further_reading.md pages

These are always static — no code execution. Simply omit the `kernelspec` from their
frontmatter and the JupyterLite power button will not appear.
