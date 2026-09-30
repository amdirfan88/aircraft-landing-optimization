import pandas as pd
from pathlib import Path

import matplotlib.pyplot as plt


# ============================================================
# 1. LOAD INPUT DATA AND GUROBI RESULT
# ============================================================

aircraft = pd.read_csv("data/processed/aircraft.csv")

separation = pd.read_csv(
    "data/processed/separation.csv",
    index_col=0
)

result = pd.read_csv("results/landing_schedule.csv")


# ============================================================
# 2. PREPARE DATA
# ============================================================

E = aircraft["earliest"].to_numpy()
T = aircraft["target"].to_numpy()
L = aircraft["latest"].to_numpy()

c_early = aircraft["early_penalty"].to_numpy()
c_late = aircraft["late_penalty"].to_numpy()

S = separation.to_numpy()

# Sort result by aircraft number so row i corresponds to aircraft i
result = result.sort_values("aircraft").reset_index(drop=True)

t = result["landing_time"].to_numpy()

n = len(aircraft)

tolerance = 1e-6


# ============================================================
# 3. CHECK LANDING WINDOWS
# ============================================================

window_violations = []

for i in range(n):

    if t[i] < E[i] - tolerance or t[i] > L[i] + tolerance:

        window_violations.append({
            "aircraft": i + 1,
            "earliest": E[i],
            "landing_time": t[i],
            "latest": L[i]
        })


# ============================================================
# 4. CHECK SAFETY SEPARATION
# ============================================================

separation_violations = []

for i in range(n):

    for j in range(i + 1, n):

        # Aircraft i lands first
        if t[i] < t[j]:

            actual = t[j] - t[i]
            required = S[i, j]

            if actual < required - tolerance:

                separation_violations.append({
                    "first_aircraft": i + 1,
                    "second_aircraft": j + 1,
                    "actual_separation": actual,
                    "required_separation": required
                })

        # Aircraft j lands first
        elif t[j] < t[i]:

            actual = t[i] - t[j]
            required = S[j, i]

            if actual < required - tolerance:

                separation_violations.append({
                    "first_aircraft": j + 1,
                    "second_aircraft": i + 1,
                    "actual_separation": actual,
                    "required_separation": required
                })

        # Same landing time is impossible on one runway
        else:

            separation_violations.append({
                "first_aircraft": i + 1,
                "second_aircraft": j + 1,
                "actual_separation": 0,
                "required_separation": min(S[i, j], S[j, i])
            })


# ============================================================
# 5. RECALCULATE EARLINESS, LATENESS AND PENALTY
# ============================================================

calculated_early = []
calculated_late = []
calculated_penalty = []

for i in range(n):

    early = max(T[i] - t[i], 0)
    late = max(t[i] - T[i], 0)

    penalty = (
        c_early[i] * early
        + c_late[i] * late
    )

    calculated_early.append(early)
    calculated_late.append(late)
    calculated_penalty.append(penalty)


# ============================================================
# 6. COMPARE AGAINST SAVED RESULT
# ============================================================

result_violations = []

for i in range(n):

    if (
        abs(result.loc[i, "earliness"] - calculated_early[i]) > tolerance
        or
        abs(result.loc[i, "lateness"] - calculated_late[i]) > tolerance
        or
        abs(result.loc[i, "penalty"] - calculated_penalty[i]) > tolerance
    ):

        result_violations.append(i + 1)


# ============================================================
# 7. REPORT
# ============================================================

print("\n========== SOLUTION VALIDATION ==========\n")

if len(window_violations) == 0:
    print("Landing windows:       PASSED")
else:
    print("Landing windows:       FAILED")
    print(pd.DataFrame(window_violations))


if len(separation_violations) == 0:
    print("Safety separation:     PASSED")
else:
    print("Safety separation:     FAILED")
    print(pd.DataFrame(separation_violations))


if len(result_violations) == 0:
    print("Penalty calculations:  PASSED")
else:
    print("Penalty calculations:  FAILED")
    print("Aircraft:", result_violations)


# Total objective calculated independently from CSV
total_penalty = sum(calculated_penalty)

print(f"\nRecalculated objective: {total_penalty:.2f}")


# ============================================================
# 8. FINAL VERDICT
# ============================================================

valid = (
    len(window_violations) == 0
    and len(separation_violations) == 0
    and len(result_violations) == 0
)

print("\n-----------------------------------------")

if valid:
    print("VALID SOLUTION: ALL CHECKS PASSED")
else:
    print("INVALID SOLUTION: CHECKS FAILED")

print("-----------------------------------------")



# ============================================================
# PLOT 
# ============================================================


# Load optimized result
df = pd.read_csv("results/landing_schedule.csv")

output_dir = Path("results/plots")
output_dir.mkdir(parents=True, exist_ok=True)


# ============================================================
# PLOT 1: TARGET VS OPTIMIZED LANDING TIME
# ============================================================

df_aircraft = df.sort_values("aircraft")

plt.figure(figsize=(12, 6))

plt.plot(
    df_aircraft["aircraft"],
    df_aircraft["target"],
    marker="o",
    label="Target time"
)

plt.plot(
    df_aircraft["aircraft"],
    df_aircraft["landing_time"],
    marker="o",
    label="Optimized landing time"
)

plt.xlabel("Aircraft")
plt.ylabel("Time")
plt.title("Target vs. Optimized Landing Times")
plt.legend()
plt.grid(alpha=0.3)
plt.tight_layout()

plt.savefig(
    output_dir / "target_vs_optimized.png",
    dpi=300
)

plt.show()


# ============================================================
# PLOT 2: PENALTY BY AIRCRAFT
# ============================================================

plt.figure(figsize=(12, 6))

plt.bar(
    df_aircraft["aircraft"],
    df_aircraft["penalty"]
)

plt.xlabel("Aircraft")
plt.ylabel("Penalty")
plt.title("Landing Penalty by Aircraft")
plt.grid(axis="y", alpha=0.3)
plt.tight_layout()

plt.savefig(
    output_dir / "penalty_by_aircraft.png",
    dpi=300
)

plt.show()

# ============================================================
# PLOT 3: DISTRIBUTION OF LANDING DEVIATIONS
# ============================================================

df["deviation"] = df["landing_time"] - df["target"]

plt.figure(figsize=(10, 6))

plt.hist(
    df["deviation"],
    bins=15,
    edgecolor="black"
)

plt.axvline(
    0,
    linestyle="--",
    linewidth=2,
    label="Target time"
)

plt.xlabel("Deviation from Target Time")
plt.ylabel("Number of Aircraft")
plt.title("Distribution of Landing Time Deviations")
plt.legend()
plt.grid(axis="y", alpha=0.3)
plt.tight_layout()

plt.savefig(
    output_dir / "landing_deviation_histogram.png",
    dpi=300
)

plt.show()
