# Gittins.py — README

This script implements two bandit models used in the advisor experiment: the **infinite-horizon Gittins index** (single arm) and the **finite 20-round two-armed bandit** (optimal policy and value). It uses the same accuracy levels and priors as the experiment (Dots & Co. vs PixelHouse).

---

## What it does

1. **Infinite-horizon Gittins index**  
   For a single arm (one advisor), it computes the **Gittins index** at each belief state: the retirement value λ such that you are indifferent between “retire and get λ every period forever” and “continue with this arm.”  
   The script builds a heatmap of this index over a grid of (successes, failures) for the Dots prior.

2. **20-round finite-horizon DP**  
   For the **two-armed bandit** (choose Dots or Pixel each round, 20 rounds total), it solves the Bellman equation via dynamic programming and reports the **optimal expected number of correct answers** from the start of the block.

3. **Figures**  
   If matplotlib and seaborn are installed, it saves:
   - `gittins_map.png` — Gittins index for each (wins, losses) cell.
   - `information_bonus.png` — Gittins index minus myopic value (expected accuracy), i.e. “information bonus” from learning.

---

## Parameters (match the experiment)

| Variable       | Meaning |
|----------------|--------|
| `accuracies`   | Possible advisor accuracies: 90%, 75%, 60%, 50%. |
| `prior_dots`   | Dots & Co. prior over those accuracies: (0.3, 0.3, 0.2, 0.2). |
| `prior_pixel`  | PixelHouse prior: (0.2, 0.2, 0.3, 0.3). |
| `gamma`        | Discount factor for the infinite-horizon problem (0.95). |
| `T_MAX`        | Number of rounds in the finite problem (20). |

Beliefs are 4-dimensional probability vectors over the four accuracy levels. After \(s\) successes and \(f\) failures, the posterior is computed by Bayes’ rule (binomial likelihood for each accuracy).

---

## Main functions

### Belief and reward

- **`get_mu(p)`**  
  Expected immediate reward (probability of a correct prediction) under belief `p`:  
  \(\mu = \sum_k p_k \cdot \text{accuracy}_k\).

- **`update_p(p, s, f)`**  
  Bayesian update of belief `p` after `s` successes and `f` failures (binomial likelihood; posterior is normalized).

### Infinite-horizon Gittins

- **`get_gittins(p_init)`**  
  Returns the Gittins index for belief `p_init`.

  - **Idea:** You can either “retire” and receive a constant λ per period (present value λ/(1−γ)), or “continue” with this arm: get μ this period and then the discounted continuation value.
  - **Bellman:**  
    \(V(\lambda, p) = \max\bigl\{ \lambda/(1-\gamma),\ \mu(p) + \gamma\bigl[\mu(p)\,V(\lambda,p_{\text{succ}}) + (1-\mu(p))\,V(\lambda,p_{\text{fail}})\bigr]\bigr\}\).
  - **Implementation:** Binary search on λ so that the optimal action is indifference (value of continuing equals value of retiring). Memoization over (λ, rounded p) keeps runs fast.

### 20-round finite-horizon DP

- **`get_dp_val_discrete(s1, f1, s2, f2, rounds_left)`**  
  Optimal expected total correct answers from the current state to the end of the 20 rounds.

  - **State:**  
    - \((s_1, f_1)\): successes and failures so far for arm 1 (Dots).  
    - \((s_2, f_2)\): same for arm 2 (Pixel).  
    - `rounds_left`: number of rounds remaining.
  - **Priors:** Reconstructed from these counts and the initial priors `prior_dots` and `prior_pixel`.
  - **Recurrence:** At each step, choose arm 1 or 2; reward is 1 if correct, 0 if wrong; no discounting (total undiscounted correct answers over 20 rounds).

- **`get_dp_val(p1, p2, rounds_left)`**  
  Wrapper used at **block start** (no observations yet): calls `get_dp_val_discrete(0, 0, 0, 0, rounds_left)`.

---

## Output

When you run the script:

1. **Console:**  
   - Gittins index at the Dots prior.  
   - 20-round optimal expected correct (from start, both arms).  
   - Message that figures were saved (if plotting is available).

2. **Files (if matplotlib/seaborn installed):**  
   - `gittins_map.png` — Heatmap of Gittins index vs (wins, losses).  
   - `information_bonus.png` — Heatmap of (Gittins − myopic value).

If matplotlib or seaborn is missing, the script still computes and prints the two numbers and asks you to install them for figures.

---

## How to run

From the `advisor_experiment` directory:

```bash
python Gittins.py
```

**Dependencies:**  
- `numpy` (required).  
- `matplotlib` and `seaborn` (optional; only needed for the two PNG figures).

Install with:

```bash
pip install numpy matplotlib seaborn
```

(or use the same Python environment you use for the rest of the project).

---

## Relation to the experiment

- **Gittins index:** Theoretical benchmark for the infinite-horizon “which advisor to use” problem; the heatmaps show how the value of an arm (and the information bonus) changes as you observe more outcomes.
- **20-round DP:** Matches the **block length** in the experiment (20 rounds per block). The reported value is the expected number of correct answers under the **optimal** switching policy between the two advisors (Dots vs Pixel) over one block.
