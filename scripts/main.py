import pandas as pd
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import tkinter as tk
from tkinter import IntVar, StringVar, Frame, Label, Button, Entry
from tkinter.ttk import Checkbutton
import matplotlib.patches as mpatches
import random

# --- Load dataset ---
file_path = r"C:\Users\Sicaja\Desktop\SmartCodeACADEMY\0.0_Channel_topics\0000.00.02_DB\2.0_Usage\2024.10.06_GitHub_PRJ_Custom-Multi-Dimensional-Data-Visualizer_linear_100_v4.xlsx"
data = pd.read_excel(file_path)

# --- Metadata columns ---
color_column = "color"
source_column = "source"

unique_sources = data[source_column].unique()

# Event columns
event_columns = [col for col in data.columns if "$$" in col]
feature_names = sorted(set(col.split("$$")[0] for col in event_columns))

# --- Determine dimensionality of features ---
feature_dims = {}
for feat in feature_names:
    col_name = [c for c in event_columns if c.startswith(feat)][0]
    sample_values = str(data[col_name].dropna().iloc[0]).split(";")
    feature_dims[feat] = len(sample_values)

max_dim = max(feature_dims.values())

# Separate 2D and 3D features
features_2d = [f for f, d in feature_dims.items() if d == 2]
features_3d = [f for f, d in feature_dims.items() if d >= 3]

# --- Tkinter UI ---
root = tk.Tk()
root.title("Developed by Ivan Sicaja © 2025")
root.attributes('-topmost', True)  # keep window on top

# Checkbox vars (default: only highest dimension features selected)
checkbox_vars = {src: IntVar(value=1) for src in unique_sources}
feature_vars = {}
for f in feature_names:
    if feature_dims[f] == max_dim:
        feature_vars[f] = IntVar(value=1)
    else:
        feature_vars[f] = IntVar(value=0)

# Track figures
figures_axes = []
current_elevation = 30
current_azimuth = 45

# Figure size in inches
fig_width_in = 9.54
fig_height_in = 4.51

# --- Define 20 professional low-saturation colors ---
soft_colors = [
    "#A6CEE3", "#1F78B4", "#B2DF8A", "#33A02C", "#FB9A99", "#E31A1C",
    "#FDBF6F", "#FF7F00", "#CAB2D6", "#6A3D9A", "#FFFF99", "#B15928",
    "#8DD3C7", "#FFFFB3", "#BEBADA", "#FB8072", "#80B1D3", "#FDB462",
    "#B3DE69", "#FCCDE5"
]

# --- Map dataset colors consistently ---
sorted_sources = sorted(unique_sources)
color_dict = {}
for i, src in enumerate(sorted_sources):
    if i < len(soft_colors):
        color_dict[src] = soft_colors[i]
    else:
        # Random soft color if more than 20 datasets
        r = lambda: random.randint(100, 230)
        color_dict[src] = f'#{r():02X}{r():02X}{r():02X}'

# --- Plot Function ---
def create_plot():
    global figures_axes
    fig = plt.figure(figsize=(fig_width_in, fig_height_in))

    # Determine if 3D
    selected_feats = [f for f, var in feature_vars.items() if var.get() == 1]
    is_3d = any(feature_dims[f] >= 3 for f in selected_feats)
    ax = fig.add_subplot(111, projection='3d') if is_3d else fig.add_subplot(111)
    figures_axes.append((fig, ax))
    ax.clear()

    used_datasets = set()
    used_features = set()

    for src in unique_sources:
        if checkbox_vars[src].get() == 1:
            src_mask = data[source_column] == src
            src_color = color_dict[src]  # Use consistent color
            for col in event_columns:
                feature = col.split("$$")[0]
                if feature not in selected_feats:
                    continue
                values = data.loc[src_mask, col].dropna().astype(str).str.split(";", expand=True)
                values = values.apply(pd.to_numeric, errors="coerce")

                if is_3d and values.shape[1] >= 3:
                    ax.scatter(values[0], values[1], values[2], c=src_color, alpha=0.8)
                elif not is_3d and values.shape[1] >= 2:
                    ax.scatter(values[0], values[1], c=src_color, alpha=0.8)

                used_datasets.add((src, src_color))
                used_features.add(feature)

    # Axis labels
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    if is_3d:
        ax.set_zlabel("Time [ms]")
        ax.view_init(elev=current_elevation, azim=current_azimuth)

    # Dynamic title from entry
    title_text = title_entry.get().strip()
    ax.set_title(title_text if title_text else "Event Data Visualization")

    # Legends
    if used_datasets:
        sorted_datasets = sorted(list(used_datasets), key=lambda x: x[0])
        dataset_handles = [mpatches.Patch(color=color, label=src) for src, color in sorted_datasets]
        dataset_legend = ax.legend(handles=dataset_handles, title="Datasets:",
                                   bbox_to_anchor=(1.02, 1), loc="upper left")
        ax.add_artist(dataset_legend)

    if used_features:
        bullet_handles = [mpatches.Patch(color="none", label=f"• {f}") for f in sorted(used_features)]
        ax.legend(handles=bullet_handles, title="Features:",
                  bbox_to_anchor=(1.02, 0.5), loc="upper left")

    plt.tight_layout()

    # --- Automatic 2x2 shifting ---
    idx = len(figures_axes) - 1
    slot = idx % 4
    width_px = int(fig_width_in * fig.dpi)
    height_px = int(fig_height_in * fig.dpi)
    down_shift = int(0.15 * height_px)  # 10% downward shift for bottom row

    if slot == 0:
        x_pos, y_pos = 0, 0
    elif slot == 1:
        x_pos, y_pos = width_px, 0
    elif slot == 2:
        x_pos, y_pos = 0, height_px + down_shift
    elif slot == 3:
        x_pos, y_pos = width_px, height_px + down_shift

    fig.canvas.manager.window.wm_geometry(f"+{x_pos}+{y_pos}")
    plt.show()

# --- Rotation Function ---
def update_rotation():
    global current_elevation, current_azimuth
    try:
        current_elevation = int(elevation_degree_var.get())
        current_azimuth = int(azimuth_degree_var.get())
    except ValueError:
        return
    for fig, ax in figures_axes:
        if hasattr(ax, "view_init"):
            ax.view_init(elev=current_elevation, azim=current_azimuth)
            fig.canvas.draw()

# --- Feature selection callbacks ---
def feature_clicked(feat):
    if feat in features_2d and feature_vars[feat].get() == 1:
        # Deselect all 3D features
        for f in features_3d:
            feature_vars[f].set(0)
        elevation_entry.config(state="disabled")
        azimuth_entry.config(state="disabled")
        apply_rot_btn.config(state="disabled")
    elif feat in features_3d and feature_vars[feat].get() == 1:
        # Deselect all 2D features
        for f in features_2d:
            feature_vars[f].set(0)
        elevation_entry.config(state="normal")
        azimuth_entry.config(state="normal")
        apply_rot_btn.config(state="normal")
    else:
        # No 3D selected, disable rotation if needed
        if not any(feature_vars[f].get() == 1 for f in features_3d):
            elevation_entry.config(state="disabled")
            azimuth_entry.config(state="disabled")
            apply_rot_btn.config(state="disabled")

# --- UI Layout ---
dataset_frame = Frame(root, bd=2, relief="groove", padx=5, pady=5)
dataset_frame.pack(side="left", padx=10, pady=10, fill="y")
Label(dataset_frame, text="Select Datasets:", font=("Arial", 10, "bold")).pack(anchor="w")
for src in unique_sources:
    Checkbutton(dataset_frame, text=src, variable=checkbox_vars[src]).pack(anchor="w")

feature_frame = Frame(root, bd=2, relief="groove", padx=5, pady=5)
feature_frame.pack(side="left", padx=10, pady=10, fill="y")
Label(feature_frame, text="Select Features:", font=("Arial", 10, "bold")).pack(anchor="w")

Label(feature_frame, text="Two-Dimensional:").pack(anchor="w", pady=(5,0))
for f in features_2d:
    cb = Checkbutton(feature_frame, text=f, variable=feature_vars[f], command=lambda feat=f: feature_clicked(feat))
    cb.pack(anchor="w")

Label(feature_frame, text="Three-Dimensional:").pack(anchor="w", pady=(5,0))
for f in features_3d:
    cb = Checkbutton(feature_frame, text=f, variable=feature_vars[f], command=lambda feat=f: feature_clicked(feat))
    cb.pack(anchor="w")

control_frame = Frame(root, bd=2, relief="groove", padx=10, pady=10)
control_frame.pack(side="left", padx=10, pady=10, fill="y")

Label(control_frame, text="Custom Graph Title:", font=("Arial", 10, "bold")).pack(anchor="w")
title_entry = Entry(control_frame, width=25)
title_entry.pack(anchor="w", pady=(0,10))

Button(control_frame, text="Create Plot", font=("Arial", 10, "bold"), bg="#4CAF50", fg="white",
       command=create_plot).pack(fill="x", pady=(0,10))

Label(control_frame, text="Rotation Settings", font=("Arial", 10, "bold")).pack(anchor="w", pady=(0,5))
Label(control_frame, text="Elevation (-90° to +90°):").pack(anchor="w")
elevation_degree_var = StringVar(value=str(current_elevation))
elevation_entry = Entry(control_frame, textvariable=elevation_degree_var, width=15)
elevation_entry.pack(anchor="w", pady=(0,5))

Label(control_frame, text="Azimuth (0° to 360°):").pack(anchor="w")
azimuth_degree_var = StringVar(value=str(current_azimuth))
azimuth_entry = Entry(control_frame, textvariable=azimuth_degree_var, width=15)
azimuth_entry.pack(anchor="w", pady=(0,5))

apply_rot_btn = Button(control_frame, text="Apply Rotation", font=("Arial", 10, "bold"), bg="#2196F3", fg="white",
                       command=update_rotation)
apply_rot_btn.pack(pady=(5,0), fill="x")

# Disable rotation if no 3D features selected initially
if not any(feature_vars[f].get() == 1 for f in features_3d):
    elevation_entry.config(state="disabled")
    azimuth_entry.config(state="disabled")
    apply_rot_btn.config(state="disabled")

# --- Center interface on screen ---
root.update_idletasks()
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
total_width = dataset_frame.winfo_reqwidth() + feature_frame.winfo_reqwidth() + control_frame.winfo_reqwidth() + 40
total_height = max(dataset_frame.winfo_reqheight(), feature_frame.winfo_reqheight(), control_frame.winfo_reqheight()) + 40
x = (screen_width // 2) - (total_width // 2)
y = (screen_height // 2) - (total_height // 2)
root.geometry(f"{total_width}x{total_height}+{x}+{y}")

root.mainloop()
