# Stochastic & Distributive Approaches - Implementation Guide

## Philosophy

**Everything is probabilistic, not deterministic.** This makes the AI human-like because humans are unpredictable, inconsistent, and variable.

## Key Patterns Used

### 1. Normal Distributions (N(μ, σ))
Used for: thresholds, values, speeds, delays

```python
# Instead of fixed threshold:
threshold = 0.35  # ❌ Fixed

# Use distribution:
threshold_mean = 0.35
threshold_std = 0.1
threshold = np.random.normal(threshold_mean, threshold_std)  # ✅ Stochastic
```

**Examples:**
- Initiative thresholds: `N(0.35, 0.1)`
- Typing speeds: `N(45, 5)` WPM
- Memory similarity: `N(0.80, 0.05)`
- Energy levels: `N(circadian_mean, 0.1)`

### 2. Monte Carlo Path Sampling (MCPS)
Used for: complex decisions, scoring

```python
# Instead of single calculation:
score = base + component1 + component2  # ❌ Fixed

# Use MCPS:
samples = []
for _ in range(10):
    sample = base + np.random.normal(comp1_mean, comp1_std) + np.random.normal(comp2_mean, comp2_std)
    samples.append(sample)
score = np.mean(samples)  # ✅ Stochastic aggregation
```

**Examples:**
- Initiative scoring: 10 samples, take mean
- Empathy action scoring: multiple weight samples
- Reciprocity balance: multiple time-weight samples

### 3. Probabilistic Decisions
Used for: yes/no decisions, selections

```python
# Instead of deterministic:
if score > threshold:
    send_message()  # ❌ Always sends if above

# Use probability:
if score > threshold:
    send_prob = 0.9  # 90% chance
    if random.random() < send_prob:
        send_message()  # ✅ Probabilistic
```

**Examples:**
- Initiative sending: 90% if above threshold, 10% if close
- Phase transitions: 70% chance even if conditions met
- DND override: 70% chance if condition met
- Memory recall: probability based on salience

### 4. Range Sampling
Used for: counts, delays, multipliers

```python
# Instead of fixed:
message_count = 2  # ❌ Fixed

# Use range with distribution:
count_range = (2, 4)
count_mean = (count_range[0] + count_range[1]) / 2
count_std = (count_range[1] - count_range[0]) / 4
message_count = int(np.random.normal(count_mean, count_std))  # ✅ Sampled
```

**Examples:**
- Burst patterns: message count from (2, 4) range
- Inter-message delays: from (1, 6) seconds range
- Typing speed multipliers: from (0.9, 1.1) range

### 5. Distribution-Based Values
Used for: entry values, emotional states

```python
# Instead of fixed:
vulnerability_value = 0.5  # ❌ Fixed

# Use distribution:
vulnerability_values = {
    "small": (0.15, 0.05),      # (mean, std)
    "medium": (0.45, 0.1),
    "deep": (0.75, 0.15)
}
value_mean, value_std = vulnerability_values["medium"]
value = np.random.normal(value_mean, value_std)  # ✅ Sampled
```

**Examples:**
- Reciprocity entry values: all sampled from distributions
- Emotional state predictions: probability distributions
- Confidence scores: aggregated with variance

### 6. Impulsivity & Unpredictability
Used for: human-like randomness

```python
# Add impulsivity:
if random.random() < 0.05:  # 5% chance
    # Do something even if "shouldn't"
    send_message()  # Impulsive message

# Add variance to everything:
base_value = 0.5
variance = 0.1
actual_value = base_value + np.random.normal(0, variance)  # ✅ Varies
```

**Examples:**
- 5% chance to message even when initiative score low
- Random memory recall (5% chance)
- Variance in all calculations

## Implementation Checklist

When building new components, ensure:

- [ ] No fixed thresholds (use distributions)
- [ ] No fixed values (use ranges/distributions)
- [ ] No deterministic decisions (use probabilities)
- [ ] Add variance to calculations
- [ ] Use MCPS for complex scoring
- [ ] Add impulsivity where appropriate
- [ ] Sample from distributions, don't use means directly

## Variance Guidelines

- **High variance (0.15-0.2):** Human behavior, emotional reactions
- **Medium variance (0.1-0.15):** Thresholds, scores
- **Low variance (0.05-0.1):** Core traits, stable values

## Examples by Component

### Initiative Engine
- Initiative score: MCPS (10 samples)
- Threshold: `N(0.35, 0.1)`
- Impulsivity: 5% chance
- DND override: 70% probability

### Message Planner
- Message count: Range (2, 4) with normal distribution
- Delays: `N(mean, std)` per delay
- Typing speed: `N(45, 5)` WPM base, then multiplied
- Typo probability: Distribution based on energy

### Theory of Mind
- User state: Probability distributions
- Reply likelihood: `N(circadian_mean, 0.15)`
- Action selection: Probabilities (60% top, 25% 2nd, etc.)
- All predictions: Add noise (0.1-0.15 std)

### Reciprocity Ledger
- Entry values: All from distributions
- Time weights: `N(recent_weight, 0.15)`
- Balance: Add noise (0.05 std)
- Imbalance threshold: `N(0.4, 0.1)`

## Result

**Every decision, every value, every threshold is probabilistic.** This creates genuine human-like unpredictability and variance. The AI doesn't behave identically in identical situations - just like humans.




