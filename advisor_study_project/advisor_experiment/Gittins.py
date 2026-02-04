import numpy as np
import sys
import matplotlib.pyplot as plt  # type: ignore[import-untyped]
import seaborn as sns  # type: ignore[import-untyped]

# --- CONFIGURATION & PRIORS ---
# Defined from your problem statement
PRIOR_A = {0.8: 0.30, 0.6: 0.30, 0.4: 0.20, 0.2: 0.20}
PRIOR_B = {0.8: 0.20, 0.6: 0.20, 0.4: 0.30, 0.2: 0.30}
HORIZON = 20
SIMULATION_RUNS = 5000

# Increase recursion depth just in case, though 20 is shallow
sys.setrecursionlimit(2000)

# --- 1. THE MATH ENGINE (Dynamic Programming) ---

def get_expected_accuracy(prior):
    """Calculates expected value of an advisor given their current belief state."""
    return sum(acc * prob for acc, prob in prior.items())

def update_prior(prior, success):
    """Bayesian update of the prior."""
    new_prior = {}
    total_prob = 0.0
    for acc, prob in prior.items():
        likelihood = acc if success else (1 - acc)
        new_prior[acc] = prob * likelihood
        total_prob += new_prior[acc]
    
    # Normalize
    for acc in new_prior:
        new_prior[acc] /= total_prob
    return new_prior

# Memoization Dictionary
memo = {}

def solve_dp(sA, fA, sB, fB, priorA, priorB):
    """
    Returns the Q-values (Expected Future Reward) for choosing A and B.
    State: (wins_A, losses_A, wins_B, losses_B)
    """
    rounds_played = sA + fA + sB + fB
    if rounds_played >= HORIZON:
        return 0.0, 0.0
    
    # Check Memoization
    state_key = (sA, fA, sB, fB)
    if state_key in memo:
        return memo[state_key]

    # --- CALC VALUE FOR CHOOSING A ---
    exp_A = get_expected_accuracy(priorA)
    
    # Future if A succeeds
    pA_succ = update_prior(priorA, True)
    future_A_succ = max(solve_dp(sA + 1, fA, sB, fB, pA_succ, priorB))
    
    # Future if A fails
    pA_fail = update_prior(priorA, False)
    future_A_fail = max(solve_dp(sA, fA + 1, sB, fB, pA_fail, priorB))
    
    q_A = exp_A * (1 + future_A_succ) + (1 - exp_A) * (0 + future_A_fail)

    # --- CALC VALUE FOR CHOOSING B ---
    exp_B = get_expected_accuracy(priorB)
    
    # Future if B succeeds
    pB_succ = update_prior(priorB, True)
    future_B_succ = max(solve_dp(sA, fA, sB + 1, fB, priorA, pB_succ))
    
    # Future if B fails
    pB_fail = update_prior(priorB, False)
    future_B_fail = max(solve_dp(sA, fA, sB, fB + 1, priorA, pB_fail))
    
    q_B = exp_B * (1 + future_B_succ) + (1 - exp_B) * (0 + future_B_fail)
    
    # Store and Return
    memo[state_key] = (q_A, q_B)
    return q_A, q_B

# --- 2. GENERATE DATA FOR PLOTS ---

def generate_heatmap_data():
    print("Generating Heatmap Data (Patience Frontier)...")
    # We look at the decision boundary assuming B is still "Fresh" (0 wins, 0 losses)
    grid_size = 14
    diff_grid = np.zeros((grid_size, grid_size))
    
    for w in range(grid_size):
        for l in range(grid_size):
            if w + l >= HORIZON:
                diff_grid[l, w] = np.nan # Impossible state
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

def run_simulation():
    print(f"Running Monte Carlo Simulation ({SIMULATION_RUNS} runs)...")
    scores = []
    
    for _ in range(SIMULATION_RUNS):
        # 1. Determine True Accuracies for this specific world
        true_A = np.random.choice(list(PRIOR_A.keys()), p=list(PRIOR_A.values()))
        true_B = np.random.choice(list(PRIOR_B.keys()), p=list(PRIOR_B.values()))
        
        # 2. Play the game
        sA, fA, sB, fB = 0, 0, 0, 0
        pA, pB = PRIOR_A.copy(), PRIOR_B.copy()
        score = 0
        
        for _ in range(HORIZON):
            qA, qB = solve_dp(sA, fA, sB, fB, pA, pB)
            
            # Greedy choice on Q-values
            choice = 'A' if qA >= qB else 'B'
            
            if choice == 'A':
                is_correct = np.random.rand() < true_A
                if is_correct:
                    score += 1
                    sA += 1
                    pA = update_prior(pA, True)
                else:
                    fA += 1
                    pA = update_prior(pA, False)
            else:
                is_correct = np.random.rand() < true_B
                if is_correct:
                    score += 1
                    sB += 1
                    pB = update_prior(pB, True)
                else:
                    fB += 1
                    pB = update_prior(pB, False)
        scores.append(score)
    return scores

# --- 3. PLOTTING FUNCTION ---

def create_thesis_plots(diff_grid, scores):
    print("Generating Plots...")
    sns.set_context("paper", font_scale=1.5)
    sns.set_style("whitegrid")
    
    # --- FIGURE 1: HEATMAP ---
    fig1, ax1 = plt.subplots(figsize=(8, 6))
    
    # Custom Colormap: Red (Switch) to Blue (Stay)
    # Using a diverging palette centered at 0
    cmap = sns.diverging_palette(10, 240, as_cmap=True, center="light")
    
    sns.heatmap(diff_grid, ax=ax1, cmap=cmap, center=0, 
                annot=True, fmt=".1f", annot_kws={"size": 7},
                cbar_kws={'label': 'Expected Advantage of A vs B'},
                square=True, mask=np.isnan(diff_grid))
    
    ax1.set_title("Optimal 'Patience Frontier' (Start of Block)", fontweight='bold')
    ax1.set_xlabel("Wins by Advisor A")
    ax1.set_ylabel("Losses by Advisor A")
    ax1.invert_yaxis() # Put 0 losses at bottom
    
    # Add Text Annotations for clarity
    ax1.text(0.5, 0.5, "START", color='black', ha='center', va='center', weight='bold', fontsize=10)
    ax1.text(0.5, 1.5, "SWITCH", color='darkred', ha='center', va='center', weight='bold', fontsize=9)
    
    plt.tight_layout()
    plt.savefig("Figure1_PatienceFrontier.png", dpi=300)
    print("Saved Figure1_PatienceFrontier.png")
    
    # --- FIGURE 2: HISTOGRAM ---
    fig2, ax2 = plt.subplots(figsize=(8, 6))
    
    mean_score = np.mean(scores)
    sns.histplot(scores, bins=np.arange(4.5, 21.5, 1), kde=False, color="#2c7fb8", alpha=0.8, stat='percent')
    
    # Add Mean Line
    ax2.axvline(mean_score, color='red', linestyle='--', linewidth=2, label=f'Mean Score: {mean_score:.2f}')
    
    ax2.set_title(f"Performance Distribution (Optimal Agent)", fontweight='bold')
    ax2.set_xlabel("Total Correct Answers (out of 20)")
    ax2.set_ylabel("Frequency (%)")
    ax2.set_xticks(range(5, 21))
    ax2.legend()
    
    plt.tight_layout()
    plt.savefig("Figure2_ScoreDistribution.png", dpi=300)
    print("Saved Figure2_ScoreDistribution.png")

if __name__ == "__main__":
    # Run from the same environment where matplotlib/seaborn are installed, e.g.:
    #   cd advisor_study_project/advisor_experiment && python Gittins.py
    # If you get ModuleNotFoundError for matplotlib/seaborn, install for that Python:
    #   python -m pip install matplotlib seaborn numpy
    # 1. Populate Memoization Table (by running start state)
    print("Solving DP...")
    solve_dp(0, 0, 0, 0, PRIOR_A.copy(), PRIOR_B.copy())
    
    # 2. Get Data
    heatmap_data = generate_heatmap_data()
    simulation_scores = run_simulation()
    
    # 3. Plot (skipped if matplotlib/seaborn not installed)
    create_thesis_plots(heatmap_data, simulation_scores)
