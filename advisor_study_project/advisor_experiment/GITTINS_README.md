## `Gittins.py` – Dynamic Programming & Simulation for Advisor Choice

This script implements the **dynamic programming / Gittins-style analysis** for the advisor experiment and generates the two thesis figures:

- `Figure1_PatienceFrontier.png` – the “patience frontier” heatmap
- `Figure2_ScoreDistribution.png` – the distribution of total correct answers under the optimal policy

It is **standalone**: you run it from the command line to produce plots; it is not called by the oTree app at runtime.

---

### 1. Configuration & Priors

At the top of `Gittins.py` you define the parameters of the bandit/advisor problem:

```python
PRIOR_A = {0.8: 0.30, 0.6: 0.30, 0.4: 0.20, 0.2: 0.20}
PRIOR_B = {0.8: 0.20, 0.6: 0.20, 0.4: 0.30, 0.2: 0.20}
HORIZON = 20
SIMULATION_RUNS = 5000
```

- **`PRIOR_A` / `PRIOR_B`** – discrete priors over the true accuracy of each advisor.  
  - The keys (0.8, 0.6, 0.4, 0.2) are possible accuracy levels.  
  - The values (e.g. 0.30, 0.20) are prior probabilities for each level.
- **`HORIZON`** – number of rounds in the decision problem (and in each simulation).  
- **`SIMULATION_RUNS`** – number of Monte Carlo runs used to generate the performance distribution plot.

There is also:

```python
sys.setrecursionlimit(2000)
```

to ensure the Python recursion limit is high enough for the depth of the dynamic program.

---

### 2. Math Engine (Dynamic Programming)

This section implements the Bayesian updating and the recursive dynamic programming that computes the optimal “Gittins-like” policy.

#### `get_expected_accuracy(prior)`

```python
def get_expected_accuracy(prior):
    \"\"\"Calculates expected value of an advisor given their current belief state.\"\"\"
    return sum(acc * prob for acc, prob in prior.items())
```

Computes the expected accuracy of an advisor given a discrete prior `prior` over possible accuracies.

#### `update_prior(prior, success)`

```python
def update_prior(prior, success):
    \"\"\"Bayesian update of the prior.\"\"\"
    new_prior = {}
    total_prob = 0.0
    for acc, prob in prior.items():
        likelihood = acc if success else (1 - acc)
        new_prior[acc] = prob * likelihood
        total_prob += new_prior[acc]
    for acc in new_prior:
        new_prior[acc] /= total_prob
    return new_prior
```

Performs a simple Bayesian update on the discrete accuracy distribution:

- If the advisor’s recommendation **succeeds**, you weight each accuracy level by `acc`.  
- If it **fails**, you weight by `1 - acc`.  
- Then you renormalize so probabilities sum to 1.

#### `memo` (memoization cache)

```python
memo = {}
```

Stores previously computed dynamic programming results for each state, to avoid recomputing the same state many times.

#### `solve_dp(sA, fA, sB, fB, priorA, priorB)`

```python
def solve_dp(sA, fA, sB, fB, priorA, priorB):
    \"\"\"Returns the Q-values (Expected Future Reward) for choosing A and B.
    State: (wins_A, losses_A, wins_B, losses_B)
    \"\"\"
    rounds_played = sA + fA + sB + fB
    if rounds_played >= HORIZON:
        return 0.0, 0.0

    state_key = (sA, fA, sB, fB)
    if state_key in memo:
        return memo[state_key]

    # --- Value if we choose A now ---
    exp_A = get_expected_accuracy(priorA)

    pA_succ = update_prior(priorA, True)
    future_A_succ = max(solve_dp(sA + 1, fA, sB, fB, pA_succ, priorA=priorB))

    pA_fail = update_prior(priorA, False)
    future_A_fail = max(solve_dp(sA, fA + 1, sB, fB, pA_fail, priorB))

    q_A = exp_A * (1 + future_A_succ) + (1 - exp_A) * (0 + future_A_fail)

    # --- Value if we choose B now ---
    exp_B = get_expected_accuracy(priorB)

    pB_succ = update_prior(priorB, True)
    future_B_succ = max(solve_dp(sA, fA, sB + 1, fB, priorA, pB_succ))

    pB_fail = update_prior(priorB, False)
    future_B_fail = max(solve_dp(sA, fA, sB, fB + 1, priorA, pB_fail))

    q_B = exp_B * (1 + future_B_succ) + (1 - exp_B) * (0 + future_B_fail)

    memo[state_key] = (q_A, q_B)
    return q_A, q_B
```

- **State**: `(sA, fA, sB, fB)` = number of correct/incorrect recommendations from A and B so far.  
- **Base case**: once `rounds_played >= HORIZON`, no future reward remains, so both Q-values are 0.  
- **Recursive case**:
  - For each possible action (choose A or B), compute:
    - Current expected reward (probability of correct advice).
    - Future value if that choice succeeds vs. fails (via recursive calls with updated priors and counts).
  - `q_A` is the expected total number of correct choices if you select A now and then follow the optimal policy thereafter; `q_B` is analogous for B.

These Q-values define the optimal policy: choose A if `q_A >= q_B`, otherwise choose B.

---

### 3. Heatmap Data (Patience Frontier)

#### `generate_heatmap_data()`

```python
def generate_heatmap_data():
    print(\"Generating Heatmap Data (Patience Frontier)...\")
    # We look at the decision boundary assuming B is fresh (0 wins, 0 losses)
    grid_size = 14
    diff                                                  = np.zeros((grid_size, grid_size))

    for w in range(grid_size):
        for l in range(g+
            if w + l >= HORIZON:
                diff_grid[l, w] = np.nan 
                continue

            # Reconstruct A's prior for this specific grid cell
            curr_pA = PRIOR_A.copy()
            for _ in range(w): curr_pA = update_prior(curr_pA, True)
            for _ in range(l): curr_pA = update_prior(curr_pA, False)

            # Get Q-values assuming B is fresh (0,0)
            qA, qB = solve_dp(w, l, 0, 0, curr_pA, PRIOR_B)

            # Store difference: Positive = Stay A, Negative = Switch B
            diff_grid[l, w] = qA - qB

    return diff_grid
```

For each possible combination of **wins (w)** and **losses (l)** for advisor A (with B still at (0,0)):

- Rebuild A’s posterior using `update_prior` applied `w` successes and `l` failures to `PRNORS`.\nescription of what `Gittins.py` does, its key variables, and its functions/methods. Let me know if you want me to save this as a file (e.g. `GITTINS_README.md`) in the `advisor_experiment` folder or tweak the wording for your advisor.</commentary>
