---
title: Project Booklet
jupyter: false
---

# Project Booklet

This section contains the project materials for the course.

## How to structure your project booklet

Add your project guidance documents to the `projects/` directory and register
them in `project.toc` in `myst.yml` under a "Project Booklet" section:

```yaml
- title: Project Booklet
  children:
    - file: projects/README.md
    - file: projects/project_guidance.md
    - file: projects/datasets.md
```

## Template placeholder

Replace this file with your actual project introduction. Include:

- Overview of the project format
- Timeline and milestones
- Links to datasets
- Guidance on the modelling workflow

## Typical project booklet structure

    projects/
      README.md              ← this file: project introduction
      project_guidance.md    ← detailed guidance document
      datasets.md            ← overview of available datasets
      modelingsteps/
        intro.md
        ModelingSteps_1through4.md
        ModelingSteps_5through10.md
