---
title: "Tutorial 5: Working with Data Files"
kernelspec:
  name: python3
  display_name: Python 3
---

# Tutorial 5: Working with Data Files

This tutorial demonstrates how to work with data files in your course using the `{nma-data}` directive.

## Declaring Data Files

The `{nma-data}` directive tells the course kit which files your tutorial needs:

:::{nma-data}
data/spike_times.npz
data/neuron_metadata.npz
:::

This declaration:
- **In the browser**: embeds files ≤2MB into the page (they load instantly from memory)
- **In notebooks**: generates a hidden download cell that fetches them from GitHub

Files must live in `data/` or `images/` inside your day's folder.

## Loading Data

Load the data the same way in both environments - normal NumPy works:

```{code-cell} python
import numpy as np

# Load spike data (allow_pickle=True needed for ragged arrays stored as object dtype)
spike_data = np.load('data/spike_times.npz', allow_pickle=True)
metadata = np.load('data/neuron_metadata.npz', allow_pickle=True)

print(f"Loaded {len(spike_data['neuron_ids'])} neurons")
print(f"Loaded {len(spike_data['trial_ids'])} trials")
print(f"Loaded {len(spike_data['condition_ids'])} conditions")
```

## Visualizing Spike Trains

Let's create a raster plot showing spike times for the first neuron across all trials:

```{code-cell} python
import matplotlib.pyplot as plt

# Get spikes for neuron 0 across all trials
n_trials = len(spike_data['trial_ids'])
neuron_idx = 0

fig, ax = plt.subplots(figsize=(10, 6))

for trial in range(n_trials):
    spike_idx = neuron_idx * n_trials + trial
    spikes = spike_data['spikes'][spike_idx]
    ax.scatter(spikes, [trial] * len(spikes), c='black', s=1, marker='|')

ax.set_xlabel('Time (s)')
ax.set_ylabel('Trial')
ax.set_title(f'{metadata["neuron_labels"][neuron_idx]} - Spike Raster')
ax.set_ylim(-1, n_trials)
plt.tight_layout()
```

## Computing Firing Rates

Calculate mean firing rate by condition:

```{code-cell} python
n_neurons = len(spike_data['neuron_ids'])
n_conditions = len(spike_data['condition_ids'])

# Compute firing rates
firing_rates = np.zeros((n_neurons, n_conditions))

for neuron in range(n_neurons):
    for trial in range(n_trials):
        spike_idx = neuron * n_trials + trial
        condition = metadata['trial_conditions'][trial]
        n_spikes = len(spike_data['spikes'][spike_idx])
        firing_rates[neuron, condition] += n_spikes / 1.0  # 1 second trials

# Average across trials
firing_rates /= (n_trials // n_conditions)

# Plot firing rates
fig, ax = plt.subplots(figsize=(8, 6))
im = ax.imshow(firing_rates, aspect='auto', cmap='viridis')
ax.set_xlabel('Condition')
ax.set_ylabel('Neuron')
ax.set_title('Mean Firing Rate by Condition')
ax.set_xticks(range(n_conditions))
ax.set_xticklabels(metadata['condition_labels'])
plt.colorbar(im, ax=ax, label='Firing Rate (Hz)')
plt.tight_layout()
```

## Interactive Exploration

Use a widget to explore different neurons and conditions:

```{code-cell} python
:tags: [hide-input]
import ipywidgets as widgets

@widgets.interact(
    neuron=widgets.IntSlider(min=0, max=19, value=0, description='Neuron'),
    condition=widgets.IntSlider(min=0, max=4, value=0, description='Condition')
)
def explore_spikes(neuron, condition):
    # Get trials for this condition
    condition_trials = np.where(metadata['trial_conditions'] == condition)[0]
    
    fig, ax = plt.subplots(figsize=(10, 4))
    
    for i, trial in enumerate(condition_trials):
        spike_idx = neuron * n_trials + trial
        spikes = spike_data['spikes'][spike_idx]
        ax.scatter(spikes, [i] * len(spikes), c='black', s=2, marker='|')
    
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Trial (within condition)')
    ax.set_title(f'{metadata["neuron_labels"][neuron]} - {metadata["condition_labels"][condition]}')
    ax.set_ylim(-1, len(condition_trials))
    plt.tight_layout()
    plt.show()
```

## Summary

When adding data to your tutorials:

1. **Create a `data/` folder** in your day's directory
2. **Keep files small** (<2MB total) so they embed in browser pages
3. **Declare files** with `{nma-data}` at the top of the tutorial
4. **Load normally** - the kit handles browser vs notebook differences
5. **Validate** with `nma-kit check` before committing

The kit automatically:
- Embeds small files for instant browser loading
- Generates download cells for Colab/Kaggle notebooks
- Validates that your code references only declared files

**Note:** This tutorial includes a `generate_data.py` script for reproducibility, but you don't need to commit data generation scripts in your own courses - just commit the data files themselves.
