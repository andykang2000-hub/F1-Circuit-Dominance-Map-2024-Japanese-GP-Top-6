"""
F1 Circuit Dominance Map — 2024 Japanese GP Qualifying
Top 6 Drivers | Suzuka Circuit

Author : Yoon
Data   : FastF1 (https://github.com/theOehrly/Fast-F1)
Output : outputs/japan_gp_dominance_map.png
"""

import os
import fastf1
import fastf1.plotting
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from matplotlib.collections import LineCollection
from matplotlib.gridspec import GridSpec

# ── Cache & session ───────────────────────────────────────────────────────────
os.makedirs('f1_cache', exist_ok=True)
os.makedirs('outputs', exist_ok=True)

fastf1.Cache.enable_cache('f1_cache')
session = fastf1.get_session(2024, 'Japan', 'Q')
session.load(laps=True, telemetry=True, weather=False, messages=False)

# ── Top 6 drivers & unique colors ────────────────────────────────────────────
drivers = ['VER', 'PER', 'NOR', 'SAI', 'ALO', 'PIA']

driver_colors = {
    'VER': '#1E41FF',   # Red Bull blue
    'PER': '#00BFFF',   # Cyan — distinct from VER
    'NOR': '#FF8000',   # McLaren orange
    'PIA': '#FFD700',   # Gold — distinct from NOR
    'SAI': '#E8002D',   # Ferrari red
    'ALO': '#00A39A',   # Aston Martin teal
}

# ── Load fastest lap + telemetry for each driver ──────────────────────────────
driver_data = {}
for drv in drivers:
    lap = session.laps.pick_drivers(drv).pick_fastest()
    tel = lap.get_telemetry(frequency='original').add_distance()
    tel = tel.merge_channels(lap.get_pos_data())
    driver_data[drv] = {'lap': lap, 'tel': tel, 'color': driver_colors[drv]}
    print(f"{drv} loaded — {lap['LapTime']}")

# ── Common distance axis (VER as reference) ───────────────────────────────────
ref_tel     = driver_data['VER']['tel']
x           = ref_tel['X'].values
y           = ref_tel['Y'].values
common_dist = np.linspace(0, ref_tel['Distance'].max(), 1000)

# Interpolate all drivers' speeds onto common distance axis
speed_matrix = {}
for drv in drivers:
    tel = driver_data[drv]['tel']
    speed_matrix[drv] = np.interp(
        common_dist,
        tel['Distance'].values,
        tel['Speed'].values
    )

# Interpolate X/Y onto common distance axis
x_common = np.interp(common_dist, ref_tel['Distance'].values, x)
y_common = np.interp(common_dist, ref_tel['Distance'].values, y)

# ── Dominance: fastest driver at each point ───────────────────────────────────
speed_array    = np.array([speed_matrix[drv] for drv in drivers])
fastest_idx    = np.argmax(speed_array, axis=0)
fastest_driver = [drivers[i] for i in fastest_idx]

dominance = {
    drv: np.sum(np.array(fastest_driver) == drv) / len(fastest_driver) * 100
    for drv in drivers
}

# ── VER vs PER direct comparison ─────────────────────────────────────────────
ver_speed = speed_matrix['VER']
per_speed = speed_matrix['PER']

# ── Suzuka corner annotations ─────────────────────────────────────────────────
corners = {
    'T1':       150,
    'Esses':    600,
    'Dunlop':   900,
    'Degner 1': 1250,
    'Degner 2': 1450,
    'Hairpin':  1750,
    'Spoon':    2700,
    '130R':     3700,
    'Chicane':  4000,
}

corner_winner = {}
for corner, dist in corners.items():
    idx = np.argmin(np.abs(common_dist - dist))
    corner_winner[corner] = fastest_driver[idx]

# ── Shared geometry ───────────────────────────────────────────────────────────
points   = np.array([x_common, y_common]).T.reshape(-1, 1, 2)
segments = np.concatenate([points[:-1], points[1:]], axis=1)

# ── Style constants ───────────────────────────────────────────────────────────
BG   = '#ffffff'
TEXT = '#111111'
GRID = '#dddddd'


# ── Helper: corner annotations ────────────────────────────────────────────────
def annotate_corners(ax):
    for corner, dist in corners.items():
        idx = np.argmin(np.abs(common_dist - dist))
        cx, cy = x_common[idx], y_common[idx]
        ax.text(cx, cy - 150, corner,
                fontsize=7, color=TEXT, ha='center', va='top',
                bbox=dict(boxstyle='round,pad=0.2', facecolor='white',
                          edgecolor='#cccccc', alpha=0.8))


# ── Figure layout ─────────────────────────────────────────────────────────────
fig = plt.figure(figsize=(18, 26), facecolor=BG)
fig.suptitle(
    '2024 Japanese GP Qualifying — Circuit Dominance Map\nSuzuka Circuit · Top 6 Drivers',
    color=TEXT, fontsize=15, y=0.98, linespacing=1.6
)

gs = GridSpec(5, 1, figure=fig,
              height_ratios=[3.5, 1, 1.2, 1.2, 1.8],
              hspace=0.35)


# ── Panel 1: Full 6-driver dominance map ─────────────────────────────────────
ax_map = fig.add_subplot(gs[0])
ax_map.set_facecolor(BG)
ax_map.axis('off')
ax_map.set_title('Track segment colored by fastest driver at each point',
                 color='#666666', fontsize=9, pad=8)

seg_colors = [driver_data[drv]['color'] for drv in fastest_driver[:-1]]
lc = LineCollection(segments, colors=seg_colors, linewidth=5, zorder=3)
ax_map.add_collection(lc)
annotate_corners(ax_map)

legend_handles = [
    mpatches.Patch(color=driver_data[drv]['color'], label=drv)
    for drv in drivers
]
ax_map.legend(handles=legend_handles, loc='lower right', fontsize=10,
              facecolor=BG, labelcolor=TEXT, framealpha=0.8,
              title='Fastest Driver', title_fontsize=9)
ax_map.autoscale_view()
ax_map.set_aspect('equal')


# ── Panel 2: Dominance % bar chart ───────────────────────────────────────────
ax_bar = fig.add_subplot(gs[1])
ax_bar.set_facecolor(BG)

bars = ax_bar.bar(drivers,
                  [dominance[drv] for drv in drivers],
                  color=[driver_colors[drv] for drv in drivers],
                  edgecolor=GRID, linewidth=0.5)

for bar, drv in zip(bars, drivers):
    ax_bar.text(bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.5,
                f"{dominance[drv]:.1f}%",
                ha='center', va='bottom', color=TEXT, fontsize=9)

ax_bar.set_ylabel('% of Track Dominated', color=TEXT, fontsize=9)
ax_bar.set_title('Track Dominance by Driver', color=TEXT, fontsize=11)
ax_bar.tick_params(colors=TEXT)
ax_bar.set_axisbelow(True)
ax_bar.grid(axis='y', color=GRID, linewidth=0.5, linestyle='--')
for spine in ax_bar.spines.values():
    spine.set_color(GRID)


# ── Panel 3: Corner winner table ─────────────────────────────────────────────
ax_table = fig.add_subplot(gs[2])
ax_table.axis('off')
ax_table.set_facecolor(BG)
ax_table.set_title('Corner Dominance', color=TEXT, fontsize=11, pad=8)

col_labels  = list(corners.keys())
cell_text   = [[corner_winner[c] for c in col_labels]]
cell_colors = [[driver_colors[corner_winner[c]] for c in col_labels]]

table = ax_table.table(
    cellText=cell_text,
    cellColours=cell_colors,
    colLabels=col_labels,
    loc='center',
    cellLoc='center'
)
table.auto_set_font_size(False)
table.set_fontsize(10)
table.scale(1, 2.5)

for j in range(len(col_labels)):
    table[0, j].set_facecolor('#f0f0f0')
    table[0, j].set_text_props(color=TEXT, fontweight='bold')
    table[1, j].set_text_props(color='white', fontweight='bold')


# ── Panel 4: VER vs PER speed trace ──────────────────────────────────────────
ax_speed = fig.add_subplot(gs[3])
ax_speed.set_facecolor(BG)

ax_speed.plot(common_dist, ver_speed, color=driver_colors['VER'],
              label='VER', linewidth=1.3, zorder=3)
ax_speed.plot(common_dist, per_speed, color=driver_colors['PER'],
              label='PER', linewidth=1.3, alpha=0.85, zorder=3)

ax_speed.fill_between(common_dist, ver_speed, per_speed,
                      where=(per_speed > ver_speed),
                      color=driver_colors['PER'], alpha=0.2,
                      label='PER faster here')
ax_speed.fill_between(common_dist, ver_speed, per_speed,
                      where=(ver_speed >= per_speed),
                      color=driver_colors['VER'], alpha=0.2,
                      label='VER faster here')

for name, dist in {'Hairpin': 1750, 'Spoon': 2700, '130R': 3700}.items():
    ax_speed.axvline(dist, color='#999999', linewidth=0.8, linestyle='--', alpha=0.6)
    ax_speed.text(dist + 30, 82, name, color='#666666', fontsize=7.5, va='bottom')

ax_speed.set_ylabel('Speed (km/h)', color=TEXT, fontsize=9)
ax_speed.set_xlabel('Distance (m)', color=TEXT, fontsize=9)
ax_speed.set_title(
    'VER vs PER Speed Trace — PER peaks higher on straights, VER is faster through key corners',
    color=TEXT, fontsize=9)
ax_speed.tick_params(colors=TEXT)
ax_speed.legend(facecolor=BG, labelcolor=TEXT, fontsize=8, loc='lower right')
ax_speed.set_axisbelow(True)
ax_speed.grid(axis='y', color=GRID, linewidth=0.5, linestyle='--')
for spine in ax_speed.spines.values():
    spine.set_color(GRID)


# ── Panel 5: VER vs PER circuit map ──────────────────────────────────────────
ax_vp = fig.add_subplot(gs[4])
ax_vp.set_facecolor(BG)
ax_vp.axis('off')
ax_vp.set_title(
    'VER vs PER — Track Dominance Map\n(Blue = VER faster · Cyan = PER faster)',
    color=TEXT, fontsize=10, pad=8)

vp_colors = [
    driver_colors['VER'] if ver_speed[i] >= per_speed[i] else driver_colors['PER']
    for i in range(len(common_dist) - 1)
]
lc_vp = LineCollection(segments, colors=vp_colors, linewidth=5, zorder=3)
ax_vp.add_collection(lc_vp)
annotate_corners(ax_vp)

vp_handles = [
    mpatches.Patch(color=driver_colors['VER'],
                   label=f"VER faster ({np.sum(ver_speed >= per_speed) / len(ver_speed) * 100:.1f}%)"),
    mpatches.Patch(color=driver_colors['PER'],
                   label=f"PER faster ({np.sum(per_speed > ver_speed) / len(per_speed) * 100:.1f}%)")
]
ax_vp.legend(handles=vp_handles, loc='lower right', fontsize=9,
             facecolor=BG, labelcolor=TEXT, framealpha=0.8)
ax_vp.autoscale_view()
ax_vp.set_aspect('equal')


# ── Save ─────────────────────────────────────────────────────────────────────
out_path = 'outputs/japan_gp_dominance_map.png'
plt.savefig(out_path, dpi=150, bbox_inches='tight', facecolor=BG)
plt.show()
print(f"Saved: {out_path}")
