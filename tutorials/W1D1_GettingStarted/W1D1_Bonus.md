---
title: "Bonus: Advanced MyST — Tabs, Dropdowns, Proofs"
---

# Bonus: Advanced MyST

## Tabbed content

Use tab-set to show alternative versions of the same content.
In MyST, wrap tab-item directives inside a tab-set directive.

Example syntax:

    ````{tab-set}
    ```{tab-item} Python
    print("Hello from Python")
    ```
    ```{tab-item} Julia
    println("Hello from Julia")
    ```
    ````

## Dropdown (collapsible) blocks

Hide answers or supplementary details:

```{dropdown} Click to reveal the solution

Here is the solution to the exercise. Use dropdowns to hide answers that students
should try themselves first.
```

## Proof environments

To use proof environments, install the sphinx-proof extension.
Add to myst.yml:

    project:
      extensions:
        - sphinx-proof

And add sphinx-proof to requirements.txt.

Then you can write:

    ```{prf:theorem} Bayes Theorem
    :label: thm-bayes

    P(A|B) = P(B|A) P(A) / P(B)
    ```

## Margin notes

Use the margin directive for asides, definitions, or links:

```{margin}
Margin notes appear in the right gutter on wide screens.
```

Main content continues here alongside the margin note.

## Footnotes

Use standard Markdown footnote syntax[^fn1].

[^fn1]: This footnote appears at the bottom of the page.
