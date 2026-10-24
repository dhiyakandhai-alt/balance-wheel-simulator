"""
Balance wheel simulator, part 1: the ticking oscillator.

Models a mechanical watch balance wheel and hairspring as a damped
harmonic oscillator. The escapement gives it a small kick every time
it swings through the centre, which keeps it going.

Run from the project folder with:  python balance_wheel.py
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# ---- Watch settings ----
BEAT_RATE_VPH = 28_800              # beats (vibrations) per hour, a common modern rate
FREQ = BEAT_RATE_VPH / 3600 / 2     # full swings per second: 2 beats per swing = 4 Hz
OMEGA0 = 2 * np.pi * FREQ           # natural angular frequency, rad/s
Q = 250                             # quality factor: higher = less energy lost per swing
KICK = 0.75                         # escapement impulse, rad/s added at each beat
START_ANGLE = np.radians(60)        # small initial swing, like giving the watch a shake

SIM_SECONDS = 60
DT = 1e-4                           # time step, s

# ---- 1. Simulate ----
n = int(SIM_SECONDS / DT)
t = np.arange(n) * DT
theta = np.zeros(n)                 # angle, rad
omega = np.zeros(n)                 # angular velocity, rad/s
theta[0] = START_ANGLE
beats = []                          # times the escapement kicked

th, w = START_ANGLE, 0.0
for i in range(n - 1):
    accel = -OMEGA0**2 * th - (OMEGA0 / Q) * w   # hairspring pulls back, friction slows
    w += accel * DT
    new_th = th + w * DT
    if th * new_th < 0:                           # passed through the centre -> tick
        w += KICK if w > 0 else -KICK
        beats.append(t[i + 1])
    th = new_th
    theta[i + 1], omega[i + 1] = th, w

# ---- 2. Measure how well it keeps time ----
deg = np.degrees(theta)
amplitude = np.abs(deg[t > SIM_SECONDS - 1]).max()

up = np.where((theta[:-1] < 0) & (theta[1:] >= 0))[0]   # upward centre crossings
up = up[t[up] > SIM_SECONDS / 2]                         # steady state only
crossings = t[up] + DT * (-theta[up]) / (theta[up + 1] - theta[up])
period = np.diff(crossings).mean()
rate = (1 / period / FREQ - 1) * 86_400                  # seconds gained (+) or lost (-) per day

print(f"Beat rate:        {BEAT_RATE_VPH:,} vph ({FREQ:.0f} swings per second)")
print(f"Beats simulated:  {len(beats):,}")
print(f"Steady amplitude: {amplitude:.0f} degrees")
print(f"Measured period:  {period * 1000:.4f} ms (ideal {1000 / FREQ:.4f} ms)")
print(f"Timekeeping:      {rate:+.2f} s/day")

# ---- 3. Chart ----
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 7))
ax1.plot(t[::10], deg[::10], lw=0.3)
ax1.set(title="Balance wheel angle: building up to a steady swing",
        xlabel="Time (s)", ylabel="Angle (degrees)")
ax1.grid(alpha=0.3)

zoom = t > SIM_SECONDS - 0.5
ax2.plot(t[zoom], deg[zoom])
for b in beats:
    if b > SIM_SECONDS - 0.5:
        ax2.axvline(b, color="red", alpha=0.3)
ax2.set(title="Last 0.5 s: each red line is one tick from the escapement",
        xlabel="Time (s)", ylabel="Angle (degrees)")
ax2.grid(alpha=0.3)
fig.tight_layout()
fig.savefig("oscillation.png", dpi=150)

# ---- 4. Animation (slow motion) ----
SLOW_MO, FPS, ANIM_SECONDS = 20, 25, 0.5
frames = int(ANIM_SECONDS * SLOW_MO * FPS)
start = n - int(ANIM_SECONDS / DT)
frame_idx = start + (np.arange(frames) * (ANIM_SECONDS / frames) / DT).astype(int)

fig2, ax = plt.subplots(figsize=(5, 5))
ax.set_xlim(-1.3, 1.3)
ax.set_ylim(-1.35, 1.3)
ax.set_aspect("equal")
ax.axis("off")
ax.set_title(f"Balance wheel at {BEAT_RATE_VPH:,} vph ({SLOW_MO}x slow motion)")

ring = np.linspace(0, 2 * np.pi, 200)
ax.plot(np.cos(ring), np.sin(ring), lw=6, color="goldenrod")        # rim
turns = 6
phi = np.linspace(0, 2 * np.pi * turns, 600)
r = np.linspace(0.12, 0.6, 600)                                      # hairspring spiral
ax.plot(r[-1], 0, "s", color="black", ms=8)                          # stud (fixed outer end)

spokes, = ax.plot([], [], lw=3, color="goldenrod")
screws, = ax.plot([], [], "o", color="saddlebrown", ms=7)
spring, = ax.plot([], [], lw=1.2, color="steelblue")
label = ax.text(0, -1.28, "", ha="center")

def update(f):
    th = theta[frame_idx[f]]
    a = th + np.arange(3) * 2 * np.pi / 3
    spokes.set_data(np.column_stack([np.zeros(3), np.cos(a), np.full(3, np.nan)]).ravel(),
                    np.column_stack([np.zeros(3), np.sin(a), np.full(3, np.nan)]).ravel())
    s = th + np.arange(8) * np.pi / 4
    screws.set_data(np.cos(s), np.sin(s))
    ang = phi + th * (1 - phi / phi[-1])     # inner end turns with wheel, outer end fixed
    spring.set_data(r * np.cos(ang), r * np.sin(ang))
    label.set_text(f"angle {np.degrees(th):+6.0f} degrees")
    return spokes, screws, spring, label

anim = FuncAnimation(fig2, update, frames=frames, interval=1000 / FPS, blit=False)
print("Saving animation (takes about 30 seconds)...")
anim.save("balance.gif", writer="pillow", fps=FPS)
plt.show()