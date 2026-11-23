"""ReplayMod camera paths for the launch video (editable source of every shot).
Each shot = camera keyframes (render ms, eye, look-at) on a catmull-rom spline + a time path (render ms -> replay ms).
`python3 shots.py SHOT replay.mcpr` writes that shot's timelines.json into the replay; render it in the Replay Viewer."""
import json, math, sys, zipfile, shutil

# Neuron replay (2026_11_23_17_02_57.mcpr, view-distance 20) starts 17:02:57; events from docs/hw_demo_weight_change.txt
T0 = 17 * 3600 + 2 * 60 + 57
ev = lambda hms: int((sum(int(a) * b for a, b in zip(hms.split(":"), (3600, 60, 1))) - T0) * 1000)
LOAD4, START4, OUT4 = ev("17:04:23"), ev("17:04:28"), ev("17:06:52")
LOAD8, START8, OUT8 = ev("17:07:12"), ev("17:07:18"), ev("17:09:42")

# Brain replay (brain_takes.mcpr) starts 17:17:07; events from docs/video_brain_takes.txt
T0B = 17 * 3600 + 17 * 60 + 7
evb = lambda hms: int((sum(int(a) * b for a, b in zip(hms.split(":"), (3600, 60, 1))) - T0B) * 1000)
IDLE, RUN1 = evb("17:18:00"), evb("17:18:54")   # idle hold, then "what is seven times eight" (parietal)
BRAIN = (16, -5, 95)            # centre of the lit (-z facing) hemisphere
PARIETAL = (0, 17, 80)

REG = (982, -60, 1048)          # W0 register row (crossbar row 1)
LAMPS = (1066, -60, 1269)       # 4 output lamps (x 1060..1072)

SHOTS = {
    # live computation, slow low flyover rising into a high reveal of the whole 460 x 501 circuit
    "flyover": dict(cam=[(0, (700, -55, 1470), (780, -60, 1400)), (3500, (820, -50, 1400), (900, -61, 1340)),
                         (7000, (960, -30, 1360), (860, -61, 1300)), (10000, (1060, -5, 1380), (860, -61, 1260))],
                    time=[(0, START8 + 20000), (10000, START8 + 40000)]),
    # stored weight w0 = 4 written into the register latches
    "reg4": dict(cam=[(0, (998, -50, 1068), REG), (5000, (990, -54, 1060), REG)],
                 time=[(0, LOAD4 - 1000), (5000, LOAD4 + 6000)]),
    # computation time-lapse (about 30x), wide
    "lapse4": dict(cam=[(0, (1090, -25, 1150), (980, -61, 1240)), (5000, (1100, -30, 1210), (1000, -61, 1260))],
                   time=[(0, START4 + 2000), (5000, OUT4 - 4000)]),
    # output lamps update to 4 (0100)
    "out4": dict(cam=[(0, (1066, -53, 1257), LAMPS), (4000, (1066, -55, 1260), LAMPS)],
                 time=[(0, OUT4 - 4000), (4000, OUT4 + 2000)]),
    "reg8": dict(cam=[(0, (998, -50, 1068), REG), (5000, (990, -54, 1060), REG)],
                 time=[(0, LOAD8 - 1000), (5000, LOAD8 + 6000)]),
    "out8": dict(cam=[(0, (1066, -53, 1257), LAMPS), (4000, (1066, -55, 1260), LAMPS)],
                 time=[(0, OUT8 - 4000), (4000, OUT8 + 2000)]),
    # --- brain world (the separate hybrid 8-16-8 brain) ---
    # hook: extreme close-up on the cortex, dramatic pull back
    "hook": dict(cam=[(0, (0, 18, 50), (0, 18, 75)), (2500, (5, 10, 15), BRAIN), (5000, (10, 2, -20), BRAIN)],
                 time=[(0, IDLE), (5000, IDLE + 5000)]),
    # three-quarter orbit in front of the lit hemisphere
    "reveal": dict(cam=[(0, (-58, 8, 25), BRAIN), (3000, (16, 14, -5), BRAIN), (6000, (88, 8, 30), BRAIN)],
                   time=[(0, IDLE + 8000), (6000, IDLE + 14000)]),
    # real activation after RUN: slow push toward parietal, real time
    "activate": dict(cam=[(0, (-8, 6, 20), PARIETAL), (8000, (-2, 14, 42), PARIETAL)],
                     time=[(0, RUN1 + 7000), (8000, RUN1 + 15000)]),
    # final hero: slow rising pullback, whole brain in frame
    "hero": dict(cam=[(0, (16, 20, -25), BRAIN), (6000, (16, 32, -55), BRAIN)],
                 time=[(0, IDLE + 20000), (6000, IDLE + 26000)]),
}


def rot(eye, at):
    dx, dy, dz = (a - e for a, e in zip(at, eye))
    return [math.degrees(math.atan2(-dx, dz)), -math.degrees(math.atan2(dy, math.hypot(dx, dz))), 0.0]


def timelines(s):
    tp = {"keyframes": [{"time": t, "properties": {"timestamp": r}} for t, r in s["time"]],
          "segments": [0] * (len(s["time"]) - 1), "interpolators": [{"type": "linear", "properties": ["timestamp"]}]}
    rots = [rot(e, a) for _, e, a in s["cam"]]
    for p, q in zip(rots, rots[1:]):                 # unwrap yaw so the spline never spins the long way round
        q[0] += 360 * round((p[0] - q[0]) / 360)
    cp = {"keyframes": [{"time": t, "properties": {"camera:position": [e[0] + .5, e[1], e[2] + .5], "camera:rotation": r}}
                        for (t, e, a), r in zip(s["cam"], rots)],
          "segments": [0] * (len(s["cam"]) - 1),
          "interpolators": [{"type": {"type": "catmull-rom-spline", "alpha": 0.5}, "properties": ["camera:position", "camera:rotation"]}]}
    return {"": [tp, cp]}


# One render per replay: shots in replay-time order, joined by 1 ms hard cuts (linear segment), each shot its own spline.
REELS = {"neuron": ["reg4", "lapse4", "out4", "reg8", "flyover", "out8"], "brain": ["hook", "reveal", "hero", "activate"]}


def reel(names):
    """Concatenate shots; returns (timelines dict, [(name, start_ms, end_ms)] in render time)."""
    tk, ck, tseg, cseg, cint, cuts, t0 = [], [], [], [], [{"type": "linear", "properties": ["camera:position", "camera:rotation"]}], [], 0
    for n in names:
        tl = timelines(SHOTS[n])[""]; tp, cp = tl
        if tk: t0 += 1; tseg.append(0); cseg.append(0)            # the cut: 1 ms linear jump
        cint.append(cp["interpolators"][0]); k = len(cint) - 1
        for f in tp["keyframes"]: tk.append({"time": f["time"] + t0, "properties": f["properties"]})
        for f in cp["keyframes"]: ck.append({"time": f["time"] + t0, "properties": f["properties"]})
        tseg += [0] * (len(tp["keyframes"]) - 1); cseg += [k] * (len(cp["keyframes"]) - 1)
        end = t0 + tp["keyframes"][-1]["time"]; cuts.append((n, t0, end)); t0 = end
    lin = [{"type": "linear", "properties": ["timestamp"]}]
    return {"": [{"keyframes": tk, "segments": tseg, "interpolators": lin},
                 {"keyframes": ck, "segments": cseg, "interpolators": cint}]}, cuts


def inject(mcpr, name):
    tmp = mcpr + ".tmp"
    with zipfile.ZipFile(mcpr) as zi, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zo:
        for it in zi.infolist():
            if it.filename != "timelines.json": zo.writestr(it, zi.read(it.filename))
        zo.writestr("timelines.json", json.dumps(reel(REELS[name])[0] if name in REELS else timelines(SHOTS[name])))
    shutil.move(tmp, mcpr)


if __name__ == "__main__":
    inject(sys.argv[2], sys.argv[1]); print("wrote", sys.argv[1], "into", sys.argv[2])
