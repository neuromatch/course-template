import numpy as np

def generate_spike_data(n_neurons=20, n_trials=100, n_conditions=5, seed=42):
    """Generate simulated spike train data.
    
    Returns two .npz files:
    - spike_times.npz: ragged array of spike times
    - neuron_metadata.npz: experimental metadata
    """
    np.random.seed(seed)
    
    # Assign trials to conditions
    trial_conditions = np.repeat(np.arange(n_conditions), n_trials // n_conditions)
    
    # Generate spike times (ragged arrays)
    spikes = []
    for neuron in range(n_neurons):
        for trial in range(n_trials):
            # Base firing rate varies by condition
            base_rate = 10 + trial_conditions[trial] * 5  # Hz
            # Duration: 1 second
            n_spikes = np.random.poisson(base_rate)
            spike_times = np.sort(np.random.uniform(0, 1, n_spikes))
            spikes.append(spike_times)
    
    # Save spike data
    np.savez_compressed(
        'spike_times.npz',
        neuron_ids=np.arange(n_neurons),
        trial_ids=np.arange(n_trials),
        condition_ids=np.arange(n_conditions),
        spikes=np.array(spikes, dtype=object)
    )
    
    # Save metadata
    np.savez_compressed(
        'neuron_metadata.npz',
        neuron_labels=np.array([f"Neuron {i+1}" for i in range(n_neurons)]),
        condition_labels=np.array([f"Condition {i+1}" for i in range(n_conditions)]),
        trial_conditions=trial_conditions
    )
    
    print(f"Generated spike_times.npz and neuron_metadata.npz")

if __name__ == '__main__':
    generate_spike_data()
