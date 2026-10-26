---
title: "Bonus: Scaling to Multi-Week Courses"
---

# Bonus: Scaling to Multi-Week Courses

`nma-kit init` creates one example day. Here is how to grow it into a full course.

## Adding more days to Week 1

1. Create `tutorials/W1D4_NewTopic/` with the standard file structure:

       chapter_intro.md
       W1D4_Tutorial1.md
       W1D4_Tutorial2.md
       W1D4_Tutorial3.md
       W1D4_Bonus.md
       further_reading.md

2. Add the entries to `project.toc` in `myst.yml`:

       - file: tutorials/W1D4_NewTopic/chapter_intro.md
         children:
           - file: tutorials/W1D4_NewTopic/W1D4_Tutorial1.md
           - file: tutorials/W1D4_NewTopic/W1D4_Tutorial2.md
           - file: tutorials/W1D4_NewTopic/W1D4_Tutorial3.md
           - file: tutorials/W1D4_NewTopic/W1D4_Bonus.md
           - file: tutorials/W1D4_NewTopic/further_reading.md

3. Push to `main` — CI handles notebook generation and deployment automatically.

## Adding more weeks

Same pattern — increment the week number. (The `W{week}D{day}` names are the
Neuromatch Academy convention. The kit only needs the pages to be listed in
`project.toc`, so a course with a different structure can name folders as it likes.)

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
and register them in the TOC, with the landing page as the parent entry (don't
wrap it in a `title:` group, which would list it twice in the sidebar):

```yaml
- file: projects/README.md
  children:
    - file: projects/project_guidance.md
    - file: projects/datasets.md
```

## Splitting content across repos

For large courses where content lives in separate repos, fetch content into
`tutorials/` at build time using a `git clone` step in `.github/workflows/course.yml`
before `nma-kit check` runs. Document the fetch step clearly in the
workflow file.
