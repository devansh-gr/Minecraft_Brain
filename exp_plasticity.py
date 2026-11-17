"""Phase 2 definitive experiment. Nothing about the winner is hardcoded:
A = physical winner before training, B = runner-up by measured output, training repeats until the PHYSICAL winner changes."""
import json, sys, time, subprocess
from rcon import cmd
import test as T
R, EXP = T.R, T.EXP
CANDIDATES = [["what color is", "the sky when i", "feel sad and", "hear music?"],
              ["i feel the sound", "of music when i", "dance"], ["can you hear", "and see it?"]]

def V(): return [[T.score(f"V{j}_{k}", "brain.w") for k in range(8)] for j in range(16)]
def full_run(q):
    T.idle(); T.ask(q, wait=20)
    return dict(x=T.vec("x"), h=T.vec("h", 16), o=T.vec("o"), fired=T.fired(), lit=T.lit_regions())

phase = sys.argv[1] if len(sys.argv) > 1 else "train"
if phase == "train":
    cmd("function brain:ui/reset_learning"); cmd("function brain:ui/repair")
    base = V()
    for q in CANDIDATES:                      # first candidate whose physical decision is a unique winner with a nonzero runner-up
        before = full_run(q)
        o = before["o"]
        if len(before["fired"]) == 1 and sorted(o)[-2] > 0:
            break
    A = before["fired"][0]
    B = max((k for k in range(8) if R[k] != A), key=lambda k: (o[k], -k))
    B = R[B]
    log = dict(question=" ".join(q), lines=q, A=A, B=B, before=before, steps=[])
    print("input:", log["question"]); print("before: x", before["x"], "o", before["o"], "physical winner", before["fired"], "lit", before["lit"])
    print("A =", A, "| B (runner-up by o) =", B)
    cmd(f"function brain:ui/target{R.index(B)}"); T.lever(10, -74, True)
    for n in range(1, 9):
        w0 = V(); cmd("function brain:ui/train"); w1 = V()
        changed = [dict(syn=f"V{j}_{k}", hidden=j, out=R[k], before=w0[j][k], after=w1[j][k])
                   for j in range(16) for k in range(8) if w0[j][k] != w1[j][k]]
        after = full_run(q)
        log["steps"].append(dict(train=n, changed=changed, run=after))
        print(f"TRAIN {n}: {len(changed)} synapses changed; rerun o {after['o']} physical winner {after['fired']} lit {after['lit']}")
        if after["fired"] == [B]:
            break
    T.lever(10, -74, False)
    log["final_weights"] = V(); log["baseline_weights"] = base
    json.dump(log, open("build/phase2.json", "w"), indent=1)
else:   # after a server restart: weights persisted, same input still selects B
    log = json.load(open("build/phase2.json"))
    w = V()
    run = full_run(log["lines"])
    log["after_restart"] = dict(weights_identical=(w == log["final_weights"]), run=run,
                                memory_newest=cmd("data get storage brain:mem list[1]").split("contents: ")[-1])
    print("weights identical to pre-restart:", w == log["final_weights"])
    print("after restart: o", run["o"], "physical winner", run["fired"], "lit", run["lit"])
    json.dump(log, open("build/phase2.json", "w"), indent=1)
