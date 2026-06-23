"""
Generate TriGuard architecture PNG for the project design PDF.
"""
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

# Palette
NAVY = "#1E2761"
NAVY_DARK = "#0F1B3D"
CORAL = "#E63946"
GOLD = "#F4A261"
PAPER = "#F7F7FA"
INK = "#1A1A2E"
ICE = "#CADCFC"
WHITE = "#FFFFFF"

fig, ax = plt.subplots(figsize=(11, 6.5))
ax.set_xlim(0, 11)
ax.set_ylim(0, 6.5)
ax.axis("off")
fig.patch.set_facecolor(PAPER)
ax.set_facecolor(PAPER)


def box(x, y, w, h, text, fill, text_color=INK, fontsize=10, bold=False,
        edge=None, sub=None, sub_color=None):
    bbox = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08",
                          linewidth=1.0, edgecolor=edge or fill, facecolor=fill)
    ax.add_patch(bbox)
    weight = "bold" if bold else "normal"
    ax.text(x + w / 2, y + h / 2 + (0.12 if sub else 0), text,
            ha="center", va="center", color=text_color,
            fontsize=fontsize, fontweight=weight, family="DejaVu Sans")
    if sub:
        ax.text(x + w / 2, y + h / 2 - 0.18, sub,
                ha="center", va="center", color=sub_color or "#666",
                fontsize=8, style="italic", family="DejaVu Sans")


def arrow(x1, y1, x2, y2, color=NAVY, lw=1.4, style="-|>"):
    a = FancyArrowPatch((x1, y1), (x2, y2), arrowstyle=style,
                        mutation_scale=12, linewidth=lw, color=color)
    ax.add_patch(a)


# Title
ax.text(5.5, 6.2, "TriGuard — System Architecture",
        ha="center", va="center", fontsize=15, fontweight="bold",
        color=NAVY, family="DejaVu Sans")

# Row 1: Input handler
box(4.25, 5.35, 2.5, 0.55, "Input handler", "#FFFFFF", edge=ICE,
    sub="text · image · audio payload", bold=True)

# Row 2: Dispatcher
box(4.25, 4.55, 2.5, 0.55, "Modality dispatcher", NAVY, text_color=WHITE,
    sub="routes per modality", sub_color=GOLD, bold=True)
arrow(5.5, 5.35, 5.5, 5.10)

# Row 3: Three wrappers
box(0.5, 3.45, 2.8, 0.9, "Text wrapper", "#FFFFFF", edge=CORAL,
    sub="HF toxicity\nclassifier", bold=True)
box(4.1, 3.45, 2.8, 0.9, "Image wrapper", "#FFFFFF", edge=NAVY,
    sub="BLIP caption\n+ visual cues", bold=True)
box(7.7, 3.45, 2.8, 0.9, "Audio wrapper", "#FFFFFF", edge=GOLD,
    sub="Whisper transcript\n+ YAMNet tags", bold=True)

arrow(5.5, 4.55, 1.9, 4.35, color=CORAL)
arrow(5.5, 4.55, 5.5, 4.35, color=NAVY)
arrow(5.5, 4.55, 9.1, 4.35, color=GOLD)

# Row 4: Evidence schema
box(2.5, 2.45, 6.0, 0.55, "Normalised evidence schema (Pydantic)", ICE,
    text_color=NAVY, bold=True,
    sub="TextEvidence · ImageEvidence · AudioEvidence", sub_color=NAVY)
arrow(1.9, 3.45, 3.5, 3.0, color=CORAL)
arrow(5.5, 3.45, 5.5, 3.0, color=NAVY)
arrow(9.1, 3.45, 7.5, 3.0, color=GOLD)

# Row 5: LLM judge
box(3.0, 1.5, 5.0, 0.7, "Local LLM judge (Ollama)", NAVY_DARK, text_color=WHITE,
    sub="reasons over evidence · emits JSON",
    sub_color=GOLD, bold=True, fontsize=11)
arrow(5.5, 2.45, 5.5, 2.20)

# Row 6: Result
box(0.5, 0.45, 6.0, 0.7, "TriGuardResult", CORAL, text_color=WHITE,
    sub="risk score · label · flagged modalities · rationale · uncertainties · latency",
    sub_color="#FFE0E0", bold=True, fontsize=11)
arrow(5.5, 1.50, 3.5, 1.15)

# Row 6 right: Human reviewer
box(7.0, 0.45, 3.5, 0.7, "Human moderator", "#FFFFFF", edge=NAVY,
    sub="review · audit · decide", bold=True)
arrow(6.5, 0.80, 7.0, 0.80, color=CORAL, lw=1.8)

# Side: eval branch
ax.plot([8.5, 9.2, 9.2], [2.72, 2.72, 1.85], color="#888", lw=1, linestyle="--")
box(8.5, 1.3, 2.0, 0.55, "Eval harness", "#FFFFFF", edge="#888",
    sub="metrics + failures", fontsize=9)

plt.tight_layout()
out = "/sessions/adoring-relaxed-mccarthy/mnt/outputs/triguard/docs/architecture.png"
plt.savefig(out, dpi=180, bbox_inches="tight", facecolor=PAPER)
print(f"OK {out}")
