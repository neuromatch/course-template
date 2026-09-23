---
title: "Bonus: Scaling to Multi-Week Courses"
jupyter: false
---

# Bonus: Scaling to Multi-Week Courses

The template ships with one week (W1D1–W1D3). Here is how to extend it.

## Adding more days to Week 1

1. Create `tutorials/W1D4_NewTopic/` with the standard file structure:

       chapter_intro.md
       W1D4_Tutorial1.md
       W1D4_Tutorial2.md
       W1D4_Tutorial3.md
       W1D4_Bonus.md
       further_reading.md

2. Add the entries to `project.toc` in `myst.yml`:

       - title: "Day 4: New Topic"
         children:
           - file: tutorials/W1D4_NewTopic/chapter_intro.md
             children:
               - file: tutorials/W1D4_NewTopic/W1D4_Tutorial1.md
               - file: tutorials/W1D4_NewTopic/W1D4_Tutorial2.md
               - file: tutorials/W1D4_NewTopic/W1D4_Tutorial3.md
               - file: tutorials/W1D4_NewTopic/W1D4_Bonus.md
               - file: tutorials/W1D4_NewTopic/further_reading.md

3. Push to `main` — CI handles notebook generation and deployment automatically.

## Adding more weeks

Same pattern — increment the week number:

    tutorials/
      W2D1_AdvancedTopic/
      W2D2_AnotherTopic/
      W2D3_YetAnotherTopic/

Update `myst.yml` accordingly.

## Adding a precourse week

Create `tutorials/W0D1_Precourse/` for prerequisite material and register it as
the first section in the TOC before Week 1.

## Projects section

The `projects/` directory holds the project booklet. Add markdown files there
and register them under a "Project Booklet" section in the TOC:

```yaml
- title: Project Booklet
  children:
    - file: projects/README.md
    - file: projects/project_guidance.md
    - file: projects/datasets.md
```

## Splitting content across repos

For large courses where content lives in separate repos, fetch content into
`tutorials/` at build time using a `git clone` step in `generate-notebooks.yml`
before the conversion script runs. Document the fetch step clearly in the
workflow file.
