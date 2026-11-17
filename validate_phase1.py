"""Phase 1 validation against a live server (test copy of the world). Prints evidence; writes build/phase1.json."""
import json, time
from rcon import cmd
from reference import forward
import test as T

R, CH, EXP = T.R, T.CH, T.EXP
ev = {}


def sc(n, o="brain.n"):
    return T.score(n, o)


def weights():
    W = [[sc(f"W{i}_{j}", "brain.w") for j in range(16)] for i in range(8)]
    V = [[sc(f"V{j}_{k}", "brain.w") for k in range(8)] for j in range(16)]
    b = [sc(f"b{j}", "brain.w") for j in range(16)]
    c = [sc(f"c{k}", "brain.w") for k in range(8)]
    return W, b, V, c


def run_until(t_stop, lines=None, press=False):
    T.idle()
    if lines is not None:
        cmd("data merge block 2 -59 -74 {front_text:{messages:%s}}" % json.dumps((lines + ["", "", "", ""])[:4]))
    if press:      # physical console button: the tick poller must pick it up
        cmd("setblock 4 -59 -74 polished_blackstone_button[face=floor,facing=north,powered=true]")
        time.sleep(1)
        cmd("setblock 4 -59 -74 polished_blackstone_button[face=floor,facing=north,powered=false]")
    else:
        cmd("function brain:ui/run")
    while (sc("#t", "brain.st") or 0) < t_stop and sc("#state", "brain.st") == 1:
        time.sleep(0.5)


def snapshot():
    return dict(x=T.vec("x"), h=T.vec("h", 16), o=T.vec("o"))


# ---- 2 + 3: two inputs, in-game values vs independent reference using in-game weights
cmd("function brain:ui/reset_learning"); cmd("function brain:ui/repair")
for name, q in [("Q1", ["what is seven", "times eight?"]), ("Q2", ["can you hear", "and see it?"])]:
    run_until(62, q)
    g = snapshot()
    W, b, V, c = weights()
    h_ref, o_ref = forward(g["x"], W, b, V, c)
    ev[name] = dict(q=" ".join(q), game=g, ref=dict(h=h_ref, o=o_ref), match=(g["h"] == h_ref and g["o"] == o_ref))
    print(name, ev[name]["q"]); print("  game x", g["x"]); print("  game h", g["h"]); print("  ref  h", h_ref)
    print("  game o", g["o"]); print("  ref  o", o_ref); print("  match:", ev[name]["match"])

# ---- 3b: perturb weights INSIDE the game; Python only learns them by reading the scoreboard back
cmd("scoreboard players set W5_14 brain.w 7"); cmd("scoreboard players set V14_6 brain.w 9")
cmd("scoreboard players set V5_5 brain.w -3"); cmd("scoreboard players set b13 brain.w 6")
run_until(62, ["can you hear", "and see it?"])
g = snapshot(); W, b, V, c = weights(); h_ref, o_ref = forward(g["x"], W, b, V, c)
ev["Q2_perturbed"] = dict(game=g, ref=dict(h=h_ref, o=o_ref), match=(g["h"] == h_ref and g["o"] == o_ref),
                          changed="W5_14=7, V14_6=9, V5_5=-3, b13=6")
print("Q2 with in-game weights perturbed:"); print("  game h", g["h"]); print("  ref  h", h_ref)
print("  game o", g["o"]); print("  ref  o", o_ref); print("  match:", ev["Q2_perturbed"]["match"])
cmd("function brain:ui/reset_learning")

# ---- 5: physical RUN button -> network -> barrels -> comparators
run_until(T_EXC := 300, ["what is seven", "times eight?"], press=True)
time.sleep(2)
g = snapshot()
inhib = [int(cmd(f"data get block {EXP[r]['x']} -60 1 OutputSignal").split(": ")[-1]) for r in R]
decide = [int(cmd(f"data get block {EXP[r]['x']} -59 2 OutputSignal").split(": ")[-1]) for r in R]
M = int(cmd("data get block 32 -60 -1 OutputSignal").split(": ")[-1])
ev["physical"] = dict(o=g["o"], inhibitory_comparators=inhib, max_chain_M=M, decision_comparators=decide,
                      fired=T.fired())
print("physical: datapack o            ", g["o"])
print("          inhibitory comparators", inhib)
print("          max-chain end M        ", M)
print("          decision comparators   ", decide)
print("          tract heads fired      ", T.fired())
T.idle()

# ---- 6: hardware decides. Same datapack values, one comparator removed -> different winner
def inject_and_read():
    T.idle(); cmd("function brain:dbg/inject_a"); time.sleep(16)
    return T.fired(), cmd("data get entity @e[type=text_display,tag=status,limit=1] text").split("data: ")[-1]

base = inject_and_read()
x5 = EXP[CH[4]]["x"]                       # channel 5 holds 7, below the max 11
cmd(f"setblock {x5+1} -59 2 air")          # remove the comparator that feeds M into channel 5's decision side
tam = inject_and_read()
cmd(f"setblock {x5+1} -59 2 comparator[facing=east,mode=compare]")
rest = inject_and_read()
ev["hardware"] = dict(vector=[2, 5, 11, 4, 7, 3, 1, 6], intact=base, ch5_inhibition_removed=tam, restored=rest)
print("hardware test, vector [2,5,11,4,7,3,1,6]:")
print("  intact                     ->", base)
print("  ch5 inhibition comparator removed ->", tam)
print("  restored                   ->", rest)
json.dump(ev, open("build/phase1.json", "w"), indent=1)
