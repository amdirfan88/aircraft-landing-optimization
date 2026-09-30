import pandas as pd
import gurobipy as gp
from gurobipy import GRB
from pathlib import Path


# ============================================================
# 1. LOAD DATA
# ============================================================

aircraft = pd.read_csv("data/processed/aircraft.csv")

separation = pd.read_csv(
    "data/processed/separation.csv",
    index_col=0
)

n = len(aircraft)
I = range(n)

# Parameters
E = aircraft["earliest"].to_numpy()
T = aircraft["target"].to_numpy()
L = aircraft["latest"].to_numpy()

c_early = aircraft["early_penalty"].to_numpy()
c_late = aircraft["late_penalty"].to_numpy()

S = separation.to_numpy()


# ============================================================
# 2. CREATE GUROBI MODEL
# ============================================================

model = gp.Model("Aircraft_Landing")


# ============================================================
# 3. DECISION VARIABLES
# ============================================================

# Actual landing time of aircraft i
t = model.addVars(
    I,
    lb={i: E[i] for i in I},
    ub={i: L[i] for i in I},
    vtype=GRB.CONTINUOUS,
    name="landing_time"
)

# Earliness
early = model.addVars(
    I,
    lb=0,
    vtype=GRB.CONTINUOUS,
    name="early"
)

# Lateness
late = model.addVars(
    I,
    lb=0,
    vtype=GRB.CONTINUOUS,
    name="late"
)

# x[i,j] = 1 if aircraft i lands before aircraft j
# Only one binary variable is needed for each pair
x = model.addVars(
    [(i, j) for i in I for j in I if i < j],
    vtype=GRB.BINARY,
    name="precedence"
)


# ============================================================
# 4. OBJECTIVE FUNCTION
# ============================================================

model.setObjective(
    gp.quicksum(
        c_early[i] * early[i]
        + c_late[i] * late[i]
        for i in I
    ),
    GRB.MINIMIZE
)


# ============================================================
# 5. EARLINESS AND LATENESS CONSTRAINTS
# ============================================================

for i in I:

    model.addConstr(
        early[i] >= T[i] - t[i],
        name=f"early_{i}"
    )

    model.addConstr(
        late[i] >= t[i] - T[i],
        name=f"late_{i}"
    )


# ============================================================
# 6. SAFETY SEPARATION CONSTRAINTS
# ============================================================

for i in I:
    for j in I:

        if i < j:

            # Tight Big-M values
            M_ij = L[i] + S[i, j] - E[j]
            M_ji = L[j] + S[j, i] - E[i]

            # If x[i,j] = 1:
            # aircraft i lands before aircraft j
            model.addConstr(
                t[j] >=
                t[i] + S[i, j]
                - M_ij * (1 - x[i, j]),
                name=f"separation_{i}_{j}"
            )

            # If x[i,j] = 0:
            # aircraft j lands before aircraft i
            model.addConstr(
                t[i] >=
                t[j] + S[j, i]
                - M_ji * x[i, j],
                name=f"separation_{j}_{i}"
            )


# ============================================================
# 7. SOLVE
# ============================================================

model.optimize()


# ============================================================
# 8. SAVE RESULTS TO CSV
# ============================================================

if model.SolCount > 0:

    results = []

    for i in I:

        results.append({
            "aircraft": i + 1,
            "landing_time": t[i].X,
            "target": T[i],
            "earliness": early[i].X,
            "lateness": late[i].X,
            "penalty": (
                c_early[i] * early[i].X
                + c_late[i] * late[i].X
            )
        })

    results = pd.DataFrame(results)

    # Sort by actual landing time
    results = results.sort_values("landing_time")

    # Add landing sequence
    results.insert(
        0,
        "landing_order",
        range(1, len(results) + 1)
    )

    # Create output folder
    output_dir = Path("results")
    output_dir.mkdir(exist_ok=True)

    # Save CSV
    output_file = output_dir / "landing_schedule.csv"

    results.to_csv(
        output_file,
        index=False
    )

    print("\nLanding Schedule")
    print(results.to_string(index=False))

    print(f"\nObjective value: {model.ObjVal:.2f}")
    print(f"Saved to: {output_file}")

else:

    print("No feasible solution found.")
