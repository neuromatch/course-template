---
title: Project Booklet
---

# Project Booklet

This section contains the project materials for the course.

## Worked examples

Real Neuromatch project material, converted to MyST. Each shows a different kind of
page a project booklet needs:

- [Daily guide for projects](project_guidance.md) (CompNeuro): plain-Markdown guidance
  for students, with a day-by-day plan, timings and submission links. No code, so no
  `kernelspec`.
- [Macrocircuits](example_macrocircuits/Macrocircuits.md) (NeuroAI): a full project
  notebook with background, video and slides, a project-template image, setup for
  Colab/Kaggle/local, exercises and feedback widgets.
- [Guide to choosing a Neurons dataset](example_neurons/README.md) (CompNeuro): a
  dataset chooser with project-template diagrams, linking to starter pages such as
  [Allen Institute Visual Behavior](example_neurons/allen_visual_behavior.md).

The two code pages use `runtime: colab` because their dependencies (`dm_control`,
MuJoCo) or data downloads can't be assumed to work in the browser. Images are linked
from the upstream course repositories instead of being copied here, to keep this
repository small.

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

## Layout used by the examples

    projects/
      README.md                      <- this file: project introduction
      project_guidance.md            <- daily guidance for students
      example_macrocircuits/
        Macrocircuits.md             <- one full project notebook
      example_neurons/
        README.md                    <- dataset guide
        allen_visual_behavior.md     <- starter page for one dataset
