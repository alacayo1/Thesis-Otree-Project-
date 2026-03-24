import sys
import numpy as np

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt  # type: ignore[import-untyped]
    import seaborn as sns  # type: ignore[import-untyped]
    HAS_PLOTTING = True
except ImportError:
    HAS_PLOTTING = False

# Allow deep recursion for DP
sys.setrecursionlimit(5000)

# 1. SETUP PARAMETERS (match experiment: Dots & Co / PixelHouse priors)
accuracies = np.array([0.90, 0.75, 0.60, 0.50])
prior_dots = np.array([0.3, 0.3, 0.2, 0.2])
prior_pixel = np.array([0.2, 0.2, 0.3, 0.3])
gamma = 0.95
T_MAX = 20  # 20-round finite-horizon decision problem

def get_mu(p):
    """Expected immediate reward (probability of correct prediction) under prior p."""
    return np.dot(p, accuracies)

def update_p(p, s, f):
    """Bayesian update: s successes, f failures."""
    post = p * (accuracies**s) * ((1 - accuracies)**f)
    return post / np.sum(post)

# 2. INFINITE-HORIZON GITTINS INDEX (retirement / restart formulation)
def get_gittins(p_init):
    """
    Gittins index = retirement value lambda such that you're indifferent between
    retiring (get lambda per period forever) and continuing with this arm.
    Bellman: V = max( lambda/(1-gamma), mu + gamma * (mu*V(p_succ) + (1-mu)*V(p_fail)) ).
    """
    memo_v = {}

    def value_func(lambda_val, p, depth=0):
        if depth > 50:
            return get_mu(p) / (1 - gamma)
        key = (round(lambda_val, 6), tuple(np.round(p, 5)))
        if key in memo_v:
            return memo_v[key]
        mu = get_mu(p)
        v_retire = lambda_val / (1 - gamma)
        v_cont = mu + gamma * (
            mu * value_func(lambda_val, update_p(p, 1, 0), depth + 1)
            + (1 - mu) * value_func(lambda_val, update_p(p, 0, 1), depth + 1)
        )
        res = max(v_retire, v_cont)
        memo_v[key] = res
        return res

    low, high = 0.5, 0.95
    for _ in range(20):
        mid = (low + high) / 2
        v = value_func(mid, p_init)
        if v > mid / (1 - gamma):
            low = mid
        else:
            high = mid
    return (low + high) / 2

# 3. FINITE 20-ROUND DP (two-armed bandit: discrete state (s1,f1,s2,f2))
memo_dp = {}

def get_dp_val_discrete(s1, f1, s2, f2, rounds_left):
    """
    20-round optimal expected total correct answers.
    State: (s1, f1) = successes/failures on arm A (Dots), (s2, f2) = arm B (Pixel).
    rounds_left: rounds remaining. Priors are reconstructed from (s,f) + prior_dots/prior_pixel.
    """
    if rounds_left <= 0:
        return 0.0
    state = (s1, f1, s2, f2, rounds_left)
    if state in memo_dp:
        return memo_dp[state]

    p1 = update_p(prior_dots, s1, f1)
    p2 = update_p(prior_pixel, s2, f2)
    mu1, mu2 = get_mu(p1), get_mu(p2)

    v1 = mu1 + mu1 * get_dp_val_discrete(s1 + 1, f1, s2, f2, rounds_left - 1) + (1 - mu1) * get_dp_val_discrete(s1, f1 + 1, s2, f2, rounds_left - 1)
    v2 = mu2 + mu2 * get_dp_val_discrete(s1, f1, s2 + 1, f2, rounds_left - 1) + (1 - mu2) * get_dp_val_discrete(s1, f1, s2, f2 + 1, rounds_left - 1)

    res = max(v1, v2)
    memo_dp[state] = res
    return res

def get_dp_val(p1, p2, rounds_left):
    """Wrapper: compute (s,f) from priors and call discrete DP. Only valid at block start (0,0,0,0)."""
    if rounds_left <= 0:
        return 0.0
    # For "start" we have no observations yet
    return get_dp_val_discrete(0, 0, 0, 0, rounds_left)

# 4. GENERATE DATA
# 4a. Infinite-horizon Gittins index map (single arm: Dots prior, (s,f) grid)
size = 8
g_map = np.zeros((size, size))
m_map = np.zeros((size, size))

for f in range(size):
    for s in range(size):
        p_curr = update_p(prior_dots, s, f)
        g_map[f, s] = get_gittins(p_curr)
        m_map[f, s] = get_mu(p_curr)

# 4b. 20-round finite-horizon optimal value (two arms: Dots vs Pixel from start)
val_20_start = get_dp_val(prior_dots, prior_pixel, T_MAX)
print(f"Infinite-horizon Gittins: index at prior = {get_gittins(prior_dots):.4f}")
print(f"20-round optimal expected correct (from start, both arms): {val_20_start:.4f}")

# 5. PLOTTING (optional)
if HAS_PLOTTING:
    try:
        plt.style.use("seaborn-v0_8-muted")
    except Exception:
        try:
            plt.style.use("seaborn-muted")
        except Exception:
            pass

    fig, ax = plt.subplots(figsize=(8, 6))
    sns.heatmap(g_map, annot=True, fmt=".3f", cmap="RdBu_r", ax=ax)
    ax.set_title("Gittins Index Map (Infinite Horizon, Dots & Co Prior)")
    ax.set_xlabel("Wins (s)")
    ax.set_ylabel("Losses (f)")
    ax.invert_yaxis()
    plt.tight_layout()
    plt.savefig("gittins_map.png")
    plt.close()

    fig, ax = plt.subplots(figsize=(8, 6))
    sns.heatmap(g_map - m_map, annot=True, fmt=".3f", cmap="YlGnBu", ax=ax)
    ax.set_title("Information Bonus (Gittins - Myopic)")
    ax.set_xlabel("Wins (s)")
    ax.set_ylabel("Losses (f)")
    ax.invert_yaxis()
    plt.tight_layout()
    plt.savefig("information_bonus.png")
    plt.close()
    print("Figures saved: gittins_map.png, information_bonus.png")
else:
    print("Install matplotlib and seaborn to generate figures.")