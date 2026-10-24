"""
Balance wheel simulator, part 2: what makes a watch gain or lose time.

Three experiments on the same balance wheel model as part 1:
  1. Off-centre escapement impulse (Airy's theorem)
  2. Mainspring running down -> smaller swing (isochronism)
  3. Temperature, for different hairspring materials

Run from the project folder with:  python experiments.py
"""

import numpy as np
import matplotlib.pyplot as plt

BEAT_RATE_VPH = 28_800
FREQ = BEAT_RATE_VPH / 3600 / 2     # 4 swings per second
OMEGA0 = 2 * np.pi * FREQ
Q = 250
KICK = 0.75                         # escapement impulse with a fully wound mainspring


def simulate(kick=KICK, offset_deg=0.0, omega0=OMEGA0, seconds=20, dt=1e-4):
    """Run the balance wheel. Returns (rate in s/day, amplitude in degrees)."""
    d = np.radians(offset_deg)
    th = 2 * Q * kick / (np.pi * omega0)    # start near the expected steady swing
    w, t, peak = 0.0, 0.0, 0.0
    damping, w2 = omega0 / Q, omega0**2
    crossings = []

    for _ in range(int(seconds / dt)):
        w += (-w2 * th - damping * w) * dt
        new_th = th + w * dt

        if th < 0 <= new_th:                                   # timing reference
            crossings.append(t + dt * (-th) / (new_th - th))

        target = d if w > 0 else -d                            # where the kick lands
        if (th - target) * (new_th - target) < 0:
            frac = (target - th) / (new_th - th)
            k = kick if w > 0 else -kick
            w += k
            new_th += k * (1 - frac) * dt                      # apply kick mid-step

        th, t = new_th, t + dt
        if t > seconds / 2:
            peak = max(peak, abs(th))

    c = np.array(crossings)
    period = np.diff(c[c > seconds / 2]).mean()
    rate = (1 / period / FREQ - 1) * 86_400
    return rate, np.degrees(peak)


# ---- Experiment 1: off-centre impulse ----
offsets = np.arange(-20, 21, 2.5)       # degrees: negative = before centre, positive = after
rates1 = [simulate(offset_deg=o)[0] for o in offsets]
print("Experiment 1 done")

# ---- Experiment 2: mainspring running down ----
power = np.linspace(1.0, 0.5, 11)       # mainspring strength, fully wound -> half
runs2 = [simulate(kick=KICK * p, offset_deg=3) for p in power]
rates2 = [r for r, a in runs2]
amps2 = [a for r, a in runs2]
print("Experiment 2 done")

# ---- Experiment 3: temperature ----
temps = np.arange(8, 39, 5)             # 8 to 38 C, the COSC test range
REF_T = 23
# (change in hairspring stiffness per C, balance wheel expansion per C) - illustrative values
MATERIALS = {
    "Plain steel (1800s)":     (-2.4e-4, 19e-6),
    "Nivarox-type alloy":      (3.8e-5, 17e-6),
    "Compensated silicon":     (3.4e-5, 17e-6),
}
rates3 = {}
for name, (stiff, expand) in MATERIALS.items():
    rates3[name] = []
    for T in temps:
        dT = T - REF_T
        w0 = OMEGA0 * np.sqrt((1 + stiff * dT) / (1 + 2 * expand * dT))
        rates3[name].append(simulate(omega0=w0)[0])
print("Experiment 3 done\n")

# ---- Summary ----
print(f"1. Impulse 10 deg before centre: {np.interp(-10, offsets, rates1):+.1f} s/day")
print(f"   Impulse 10 deg after centre:  {np.interp(10, offsets, rates1):+.1f} s/day")
print(f"2. Fully wound: {amps2[0]:.0f} deg swing, {rates2[0]:+.1f} s/day")
print(f"   Half power:  {amps2[-1]:.0f} deg swing, {rates2[-1]:+.1f} s/day")
print("3. Rate at 8 C and 38 C:")
for name, r in rates3.items():
    print(f"   {name:<22} {r[0]:+7.1f} s/day   {r[-1]:+7.1f} s/day")

# ---- Charts ----
fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(16, 5))

ax1.plot(offsets, rates1, "o-")
ax1.axhline(0, color="grey", lw=0.8)
ax1.axvline(0, color="grey", lw=0.8)
ax1.set(title="1. Airy's theorem: off-centre impulse",
        xlabel="Where the kick lands (degrees)\n<- before centre | after centre ->",
        ylabel="Rate (seconds/day)")

ax2.plot(amps2, rates2, "o-", color="darkorange")
ax2.invert_xaxis()
ax2.set(title="2. Mainspring running down\n(kick lands 3 degrees after centre)",
        xlabel="Swing amplitude (degrees)  ->  running down", ylabel="Rate (seconds/day)")

for name, r in rates3.items():
    ax3.plot(temps, r, "o-", label=name)
ax3.set_yscale("symlog", linthresh=1)
ax3.axhline(0, color="grey", lw=0.8)
ax3.set(title="3. Temperature (COSC range 8-38 C)",
        xlabel="Temperature (C)", ylabel="Rate (seconds/day, log scale)")
ax3.legend(fontsize=9)

for ax in (ax1, ax2, ax3):
    ax.grid(alpha=0.3)
fig.tight_layout()
fig.savefig("experiments.png", dpi=150)
plt.show()