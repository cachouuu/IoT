#!/usr/bin/env python3
"""Create publication figures from the archived-evidence audit, never simulations.

Run from any directory: python scripts/make_figures.py
Optional QA PNGs: python scripts/make_figures.py --preview-dir /tmp/figure-qa
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

ROOT = Path(__file__).resolve().parents[1]
NAVY = "#1c344c"
RED = "#9e332c"
GRAY = "#5a626c"

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 8,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "axes.linewidth": 0.6,
    "xtick.major.width": 0.6,
    "ytick.major.width": 0.6,
    "savefig.facecolor": "white",
})


def save(fig, name: str, output: Path, previews: Path | None):
    metadata = {
        "Title": name.replace("_", " "),
        "Author": "Traffic Assistant DIC4",
        "Creator": "scripts/make_figures.py (Matplotlib)",
        "CreationDate": None,
        "ModDate": None,
    }
    fig.savefig(output / f"{name}.pdf", metadata=metadata)
    if previews:
        fig.savefig(previews / f"{name}.png", dpi=220)
    plt.close(fig)


def architecture(output: Path, previews: Path | None):
    fig = plt.figure(figsize=(7.0, 2.0))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set(xlim=(0, 7), ylim=(0, 2))
    ax.axis("off")
    # The separate dashed layer is not claimed as implemented runtime logic.
    ax.add_patch(FancyBboxPatch((0.08, 1.53), 6.84, 0.36,
        boxstyle="round,pad=0.025,rounding_size=0.03", linewidth=0.8,
        edgecolor=GRAY, facecolor="#fafafa", linestyle=(0, (4, 3))))
    ax.text(3.5, 1.71,
        "Planned extension: task entry  |  data qualification  |  unified reporting",
        ha="center", va="center", fontsize=9, color=GRAY)
    ax.text(0.08, 1.35, "Archived prototype architecture", va="center",
        fontsize=9, fontweight="bold", color=NAVY)
    xs = [0.08, 1.88, 3.68, 5.48]
    width, y, height = 1.44, 0.57, 0.64
    labels = [
        ("Saved synthetic", "arrival traces", "Matched fixed/model inputs"),
        ("ARM software", "FIFO + 4 features", "Tree / rule fallback"),
        ("AXI interface", "Pending plan", "One of three plan IDs"),
        ("FPGA controller", "Phase + countdown", "Apply at cycle boundary"),
    ]
    for x, (title, middle, bottom) in zip(xs, labels):
        ax.add_patch(FancyBboxPatch((x, y), width, height,
            boxstyle="round,pad=0.018,rounding_size=0.035",
            linewidth=0.8, edgecolor=NAVY, facecolor="#f4f7fa"))
        ax.text(x + width / 2, y + height - 0.15, title,
            ha="center", va="center", fontsize=9, fontweight="bold", color=NAVY)
        ax.text(x + width / 2, y + 0.30, middle,
            ha="center", va="center", fontsize=8.5, color="#20242b")
        ax.text(x + width / 2, y + 0.12, bottom,
            ha="center", va="center", fontsize=7.35, color=GRAY)
    for x, next_x in zip(xs[:-1], xs[1:]):
        ax.add_patch(FancyArrowPatch((x + width + 0.025, 0.90),
            (next_x - 0.035, 0.90), arrowstyle="-|>", mutation_scale=9,
            linewidth=0.9, color=NAVY))
    # Readback is shown explicitly; model inference is not run by the FPGA.
    arm_center, fpga_center = xs[1] + width / 2, xs[3] + width / 2
    ax.plot([fpga_center, fpga_center, arm_center], [0.545, 0.17, 0.17],
        color=GRAY, linewidth=0.8)
    ax.add_patch(FancyArrowPatch((arm_center, 0.17), (arm_center, 0.545),
        arrowstyle="-|>", mutation_scale=9, linewidth=0.8, color=GRAY))
    ax.text((arm_center + fpga_center) / 2, 0.36,
        "Active plan / cycle readback to ARM + evidence",
        ha="center", va="center", fontsize=8.2, color=GRAY)
    save(fig, "architecture", output, previews)


def scenario_changes(output: Path, previews: Path | None):
    evidence_path = ROOT / "evidence/current/audit_results.json"
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    rows = evidence["host_18_pairs"]
    scenarios = ["balanced", "ns_heavy", "ew_heavy", "direction_switch", "bursty", "overload"]
    names = ["Balanced", "NS heavy", "EW heavy", "Direction switch", "Bursty", "Overload"]
    seeds = sorted({r["seed"] for r in rows})
    if len(rows) != 18 or len(seeds) != 3:
        raise ValueError("Figure requires the complete archived six-scenario, three-seed batch.")
    if {r["scenario"] for r in rows} != set(scenarios):
        raise ValueError("Unexpected scenarios in audited evidence.")
    by_pair = {(r["scenario"], r["seed"]): r for r in rows}
    if len(by_pair) != 18:
        raise ValueError("Duplicate scenario/seed pair in audited evidence.")
    fig, ax = plt.subplots(figsize=(3.4, 2.4))
    fig.subplots_adjust(left=0.315, right=0.975, top=0.84, bottom=0.245)
    ax.axvline(0, color="#484848", linewidth=0.8, zorder=1)
    for j in range(6):
        if j % 2 == 0:
            ax.axhspan(j - 0.48, j + 0.48, facecolor="#f4f5f6", zorder=0)
    for j, scenario in enumerate(scenarios):
        for offset, seed in zip((-0.24, 0, 0.24), seeds):
            row = by_pair[(scenario, seed)]
            change = 100 * (row["model_qvs"] - row["fixed_qvs"]) / row["fixed_qvs"]
            if abs(change - row["qvs_relative_change_percent"]) > 1e-10:
                raise ValueError(f"QVS relative change mismatch: {scenario}, {seed}")
            if change <= 0:
                ax.scatter(change, j + offset, s=14, marker="o",
                    facecolor=NAVY, edgecolor=NAVY, linewidth=0.5, zorder=3)
            else:
                ax.scatter(change, j + offset, s=19, marker="^",
                    facecolor="white", edgecolor=RED, linewidth=0.9, zorder=3)
    ax.set_xlim(-87, 29)
    ax.set_ylim(5.52, -0.52)
    ax.set_yticks(range(6), names)
    ax.set_xticks([-80, -60, -40, -20, 0, 20])
    ax.tick_params(axis="both", labelsize=7.7)
    ax.tick_params(axis="y", length=0, pad=4)
    ax.tick_params(axis="x", length=3, pad=2)
    ax.set_xlabel("QVS change relative to fixed (%)", fontsize=8, labelpad=3)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.spines["bottom"].set_color("#777777")
    handles = [
        Line2D([], [], marker="o", markersize=4, linestyle="none",
               markerfacecolor=NAVY, markeredgecolor=NAVY, label="Improvement"),
        Line2D([], [], marker="^", markersize=4.6, linestyle="none",
               markerfacecolor="white", markeredgecolor=RED, label="Regression"),
    ]
    fig.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.52, 0.99),
        frameon=False, ncol=2, fontsize=8, columnspacing=1.2,
        handlelength=0.8, handletextpad=0.4, borderaxespad=0)
    # Full seed IDs are ordered by integer value: 2779054081, ...4082, ...4083.
    fig.text(0.5, 0.035, "Top to bottom in each row: seed suffixes 81, 82, 83",
             ha="center", va="bottom", fontsize=7.2, color=GRAY)
    save(fig, "scenario_changes", output, previews)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preview-dir", type=Path)
    args = parser.parse_args()
    output = ROOT / "paper/figures"
    output.mkdir(parents=True, exist_ok=True)
    previews = args.preview_dir.resolve() if args.preview_dir else None
    if previews:
        previews.mkdir(parents=True, exist_ok=True)
    architecture(output, previews)
    scenario_changes(output, previews)
    print(f"Wrote {output / 'architecture.pdf'}")
    print(f"Wrote {output / 'scenario_changes.pdf'} (18/18 archived pairs)")


if __name__ == "__main__":
    main()
