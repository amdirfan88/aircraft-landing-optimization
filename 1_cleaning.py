from pathlib import Path
import pandas as pd

input_file = Path("data/airland7.txt")
output_dir = Path("data/processed")
output_dir.mkdir(parents=True, exist_ok=True)

# Read all numbers
with open(input_file, "r") as f:
    values = f.read().split()

# Number of aircraft
n = int(values[0])

# Second value is freeze time
freeze_time = float(values[1])

pos = 2

aircraft_data = []
separation_matrix = []

for i in range(n):

    # Six 1D values for aircraft i
    appearance = float(values[pos])
    earliest = float(values[pos + 1])
    target = float(values[pos + 2])
    latest = float(values[pos + 3])
    early_penalty = float(values[pos + 4])
    late_penalty = float(values[pos + 5])

    pos += 6

    # We are not using appearance in our model
    aircraft_data.append([
        i + 1,
        earliest,
        target,
        latest,
        early_penalty,
        late_penalty
    ])

    # n separation values for aircraft i
    separation = [float(x) for x in values[pos:pos + n]]
    separation_matrix.append(separation)

    pos += n


# ---------- 1D CSV ----------

aircraft_df = pd.DataFrame(
    aircraft_data,
    columns=[
        "aircraft_id",
        "earliest",
        "target",
        "latest",
        "early_penalty",
        "late_penalty"
    ]
)

aircraft_df.to_csv(
    output_dir / "aircraft.csv",
    index=False
)


# ---------- 2D CSV ----------

separation_df = pd.DataFrame(
    separation_matrix,
    index=range(1, n + 1),
    columns=range(1, n + 1)
)

separation_df.index.name = "aircraft_id"

separation_df.to_csv(
    output_dir / "separation.csv"
)

print(f"Number of aircraft: {n}")
print("Created:")
print("  data/processed/aircraft.csv")
print("  data/processed/separation.csv")
