import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from mpl_toolkits.mplot3d import Axes3D

# -----------------------------------------------------------------------------
# 1. CONFIGURATION
# -----------------------------------------------------------------------------
INPUT_CSV = "cva6_experiments_stages_summary_final.csv"

# Baseline values to filter the data (keeping everything else constant)
BASELINE = {"ICw_num": 4, "DCw_num": 4, "BTB_num": 16, "BHT_num": 16, "RAS_num": 2}


# -----------------------------------------------------------------------------
# 2. HELPER FUNCTIONS
# -----------------------------------------------------------------------------
def parse_size(val):
    if isinstance(val, str):
        val = val.lower()
        if "k" in val:
            return int(float(val.replace("k", "")) * 1024)
        if "w" in val:
            return int(val.replace("w", ""))
        return int(val)
    return val


def format_size_label(num_bytes):
    if num_bytes >= 1024:
        return f"{int(num_bytes/1024)}k"
    return str(num_bytes)


# -----------------------------------------------------------------------------
# 3. DATA LOADING
# -----------------------------------------------------------------------------
try:
    df = pd.read_csv(INPUT_CSV)
    for col in ["IC", "ICw", "DC", "DCw", "BTB", "BHT", "RAS"]:
        if col in df.columns:
            df[f"{col}_num"] = df[col].apply(parse_size)
except FileNotFoundError:
    print(f"Error: {INPUT_CSV} not found.")
    exit()


# -----------------------------------------------------------------------------
# 4. PLOTTING FUNCTION (3D Stacked Bars)
# -----------------------------------------------------------------------------
def plot_3d_bars_interactive(df_filtered):
    if df_filtered.empty:
        print("No data found for these filters.")
        return

    metric = "BRAM"

    # Define Colors and Stages
    stages = [
        ("S1_Fetch", "Fetch", "#4e79a7"),  # Blue (Bottom)
        ("S2_Decode", "Decode", "#f28e2b"),  # Orange
        ("S3_Issue_Net", "Issue", "#e15759"),  # Red
        ("S4_Execute_Net", "Execute", "#76b7b2"),  # Cyan
        ("S5_Memory_Total", "Memory", "#59a14f"),  # Green
        ("S6_Commit", "Commit", "#edc948"),  # Yellow (Top)
    ]

    # Prepare Axes Data
    ic_sizes = sorted(df_filtered["IC_num"].unique())
    dc_sizes = sorted(df_filtered["DC_num"].unique())

    ic_map = {val: i for i, val in enumerate(ic_sizes)}
    dc_map = {val: i for i, val in enumerate(dc_sizes)}

    ic_labels = [format_size_label(x) for x in ic_sizes]
    dc_labels = [format_size_label(x) for x in dc_sizes]

    # Initialize Figure
    fig = plt.figure(figsize=(12, 10))
    ax = fig.add_subplot(111, projection="3d")

    # Draw Stacked Bars
    for _, row in df_filtered.iterrows():
        ic_val = row["IC_num"]
        dc_val = row["DC_num"]

        x_idx = ic_map[ic_val]
        y_idx = dc_map[dc_val]

        # Start stacking from Z=0 for this specific grid coordinate
        current_z = 0

        for stage_code, stage_name, stage_color in stages:
            col_name = f"{stage_code}_{metric}"
            height = row[col_name]

            if pd.notna(height) and height > 0:
                # x, y, z, dx, dy, dz
                ax.bar3d(
                    x_idx - 0.2,  # X pos (centered slightly)
                    y_idx - 0.2,  # Y pos
                    current_z,  # Z start (bottom of this segment)
                    0.4,  # Width
                    0.4,  # Depth
                    height,  # Height of this segment
                    color=stage_color,
                    shade=True,
                )

                # Move the floor up for the next pipeline stage
                current_z += height

    # Labels and Formatting
    ax.set_xticks(range(len(ic_sizes)))
    ax.set_xticklabels(ic_labels, rotation=-15, ha="left")

    ax.set_yticks(range(len(dc_sizes)))
    ax.set_yticklabels(dc_labels, rotation=15, ha="right")

    ax.set_xlabel("Instruction Cache", labelpad=15)
    ax.set_ylabel("Data Cache", labelpad=15)
    ax.set_zlabel(f"{metric} Count", labelpad=10)
    ax.set_title(f"Interactive Stacked 3D Bars: {metric} Distribution", fontsize=16)

    # Legend
    legend_handles = [
        mpatches.Patch(color=color, label=name) for _, name, color in stages
    ]
    # Reverse legend so the top stage appears at the top of the list
    ax.legend(
        handles=legend_handles[::-1],
        bbox_to_anchor=(1.05, 1),
        loc="upper left",
        title="Pipeline Stage",
    )

    # Set initial viewing angle
    ax.view_init(elev=30, azim=-60)

    # Show the interactive window
    print("Opening interactive 3D bar plot window...")
    plt.tight_layout()
    plt.show()


# -----------------------------------------------------------------------------
# 5. EXECUTE
# -----------------------------------------------------------------------------
# Filter Data
s1 = df[
    (df["ICw_num"] == BASELINE["ICw_num"])
    & (df["DCw_num"] == BASELINE["DCw_num"])
    & (df["BTB_num"] == BASELINE["BTB_num"])
    & (df["BHT_num"] == BASELINE["BHT_num"])
].copy()

# Run
plot_3d_bars_interactive(s1)
