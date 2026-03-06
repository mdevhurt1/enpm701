import matplotlib.pyplot as plt

frames = []
deltas_ms = []

with open("frame_times.txt") as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        frame, delta, *_ = line.split(",")
        frames.append(int(frame))
        deltas_ms.append(float(delta) * 1000)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

ax1.plot(frames, deltas_ms, linewidth=0.8)
ax1.set_xlabel("Frame")
ax1.set_ylabel("Delta Time (ms)")
ax1.set_title("Frame Delta Times")

ax2.hist(deltas_ms, bins=50)
ax2.set_xlabel("Delta Time (ms)")
ax2.set_ylabel("Count")
ax2.set_title("Delta Time Distribution")

plt.tight_layout()
plt.savefig("frame_times.png", dpi=150)
plt.show()
