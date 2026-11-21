"""Redstone Cortex v3 test suite. Runs against a live 26.3 server over RCON.

Usage: python3 test.py [first_test [last_test]]   -> merges results into build/test_results.json
"""
import json, random, sys, time
from rcon import cmd

EXP = json.load(open("build/expect.json"))
R = sorted(EXP, key=lambda r: EXP[r]["idx"])                   # network order
CH = sorted(EXP, key=lambda r: EXP[r]["x"])                    # physical channel order
random.seed(1)
SAMPLE = {r: random.sample(v["lit"], min(40, len(v["lit"]))) for r, v in EXP.items()}
CZ = -74
RUN_WAIT = 34


def score(name, obj="brain.n"):
    out = cmd(f"scoreboard players get {name} {obj}")
    return int(out.split(" has ")[1].split(" ")[0]) if " has " in out else None


def vec(prefix, n=8):
    return [score(f"{prefix}{i}") for i in range(n)]


def status():
    return cmd("data get entity @e[type=text_display,tag=status,limit=1] text").split("data: ")[-1]


def lit_frac(r):
    return sum("passed" in cmd(f"execute if block {x} {y} {z} redstone_lamp[lit=true]") for x, y, z in SAMPLE[r]) / len(SAMPLE[r])


def lit_regions():
    return {r: round(f, 2) for r in R if (f := lit_frac(r)) > 0}


def fired():
    return [r for r in CH if "passed" in cmd(f"execute if block {EXP[r]['x']} -59 3 repeater[powered=true]")]


def lamp_on(x, z=-70):
    return "passed" in cmd(f"execute if block {x} -59 {z} redstone_lamp[lit=true]")


def ask(lines, wait=RUN_WAIT):
    cmd("data merge block 2 -59 %d {front_text:{messages:%s}}" % (CZ, json.dumps((lines + ["", "", "", ""])[:4])))
    cmd("function brain:ui/run")
    time.sleep(wait)


def lever(x, z, on, wall=False):
    st = "face=wall,facing=west" if wall else "face=floor,facing=north"
    cmd(f"setblock {x} -59 {z} lever[{st},powered={'true' if on else 'false'}]")


def idle():
    for _ in range(40):
        if score("#state", "brain.st") == 0:
            return
        time.sleep(1)
    cmd("function brain:ui/reset")


def wait_complete(limit=40):
    """Block until the readout has run (state COMPLETE) instead of sleeping a fixed time."""
    for _ in range(limit * 2):
        if score("#state", "brain.st") == 2:
            return
        time.sleep(0.5)


RESULTS = []


def check(n, name, expected, actual, ok, how):
    RESULTS.append(dict(n=n, name=name, expected=expected, actual=str(actual), ok=bool(ok), how=how))
    print(f"[{'PASS' if ok else 'FAIL'}] {n:2d} {name}: {actual}")


def t1():
    idle(); ask(["", "", "", ""])
    f, s = fired(), status()
    check(1, "Empty input", "no channel fires, status NO WINNER, NO WINNER lamp", (f, s),
          not f and "NO WINNER" in s and lamp_on(26), "tract head repeaters + status text + indicator lamp")


def t2():
    idle(); ask(["xyzzy plugh", "frobnicate"])
    check(2, "Unknown words", "x all 0, no winner", (vec("x"), fired()), vec("x") == [0] * 8 and not fired(),
          "input scores + tract head repeaters")


def t3():
    idle(); ask(["what color is", "the sky when i", "feel sad and", "hear music?"])
    x, o, f = vec("x"), vec("o"), fired()
    best = [R[i] for i in range(8) if o[i] == max(o)]
    check(3, "Multiple region keywords", ">=3 nonzero inputs; physical winner = argmax(o)", (x, o, f),
          sum(v > 0 for v in x) >= 3 and set(f) == set(best), "x/o scores vs fired channels")


def t4():
    idle(); cmd("function brain:ui/reset_learning"); ask(["can you hear", "and see it?"])
    o, f = vec("o"), fired()
    check(4, "Equal region scores", "temporal = occipital, both fire, TIE lamp", (o, f),
          o[R.index("temporal")] == o[R.index("occipital")] and set(f) == {"temporal", "occipital"} and lamp_on(24),
          "o scores, tract heads, TIE lamp")


def t5():
    idle(); cmd("function brain:dbg/inject {c0:0,c1:0,c2:0,c3:0,c4:0,c5:0,c6:0,c7:0}"); time.sleep(RUN_WAIT - 4)
    check(5, "All-zero physical vector", "no channel fires", fired(), not fired(), "tract head repeaters")


def t5b():
    out = {}
    for key, vecv, want in [("a", [2, 5, 11, 4, 7, 3, 1, 6], [2]), ("b", [2, 11, 11, 4, 7, 3, 1, 6], [1, 2])]:
        idle(); cmd(f"function brain:dbg/inject_{key}"); wait_complete()
        out[key] = (fired(), lamp_on(24))
        out[key + "_ok"] = out[key][0] == [CH[c] for c in want] and out[key][1] == (len(want) > 1)
    check(5, "Spec vectors on the physical circuit", "[2,5,11,4,7,3,1,6] -> channel 3 only; [2,11,11,...] -> channels 2+3, TIE lamp",
          out, out["a_ok"] and out["b_ok"], "dbg/inject -> barrels -> comparator WTA -> tract heads, TIE lamp")


QS = {"prefrontal": ["should i quit", "my job?"], "broca": ["how do you say", "hello in spanish"],
      "motor": ["how fast can i", "run and jump"], "somato": ["why does my", "skin itch?"],
      "parietal": ["what is seven", "times eight?"], "temporal": ["who sang that", "song yesterday?"],
      "occipital": ["what colors are", "in a rainbow?"], "cerebellum": ["how do i keep", "my balance on", "a skateboard"]}


def t6():
    ok, got = True, {}
    for r, q in QS.items():
        idle(); ask(q)
        f, lit = fired(), lit_regions()
        got[r] = (f, lit)
        ok &= f == [r] and set(lit) == {r} and lit[r] >= 0.95
    check(6, "Each region wins", "each question fires only its channel and lights >=95% of its sampled lamps", got, ok,
          "tract heads + 40 sampled cortex lamps per region")


def t7():
    idle(); cmd("function brain:dbg/inject {c0:3,c1:9,c2:4,c3:15,c4:2,c5:8,c6:7,c7:5}"); time.sleep(RUN_WAIT - 4)
    f = fired()
    check(7, "All eight channels driven", "only channel 4 (strength 15) fires", f, f == [CH[3]], "tract heads")


def t8():
    vals = []
    for s in range(16):
        cmd(f"function brain:fill/s{s} {{x:0,y:-59,z:-28}}"); time.sleep(0.25)
        vals.append(int(cmd("data get block 0 -59 -29 OutputSignal").split(": ")[-1]))
    cmd("function brain:fill/s0 {x:0,y:-59,z:-28}")
    check(8, "Comparator levels 0..15", "comparator output equals requested level for every s", vals,
          vals == list(range(16)), "barrel fill then comparator OutputSignal")


def t9():
    idle(); cmd("function brain:ui/reset_learning"); ask(["can you hear", "and see it?"])
    occ = R.index("occipital")
    before = score("V14_6", "brain.w")
    cmd(f"function brain:ui/target{occ}"); lever(10, CZ, True); cmd("function brain:ui/train")
    after = score("V14_6", "brain.w")
    idle(); ask(["can you hear", "and see it?"])
    f = fired()
    check(9, "Training changes weights and winner", "V(A temp+occ -> occ) rises; tie becomes Visual only",
          (before, after, f), after > before and f == ["occipital"], "weight score + tract heads")


def t10():
    lever(10, CZ, False)
    before = [score(f"V{j}_6", "brain.w") for j in range(16)]
    cmd("function brain:ui/train")
    after = [score(f"V{j}_6", "brain.w") for j in range(16)]
    txt = cmd("data get entity @e[tag=train,limit=1] text")
    check(10, "Learning disabled", "TRAIN refused, weights unchanged", txt[-40:], before == after and "OFF" in txt,
          "weights before/after + training display")


def t11():
    before = [score(f"V{j}_6", "brain.w") for j in range(16)]
    cmd("reload"); time.sleep(3)
    after = [score(f"V{j}_6", "brain.w") for j in range(16)]
    check(11, "Weights survive /reload", "identical", after == before, after == before, "weights before/after reload")


def t12():
    idle()
    q0 = cmd("data get storage brain:mem list[1].q")
    cmd("function brain:ui/replay1"); time.sleep(RUN_WAIT)
    q1 = cmd("data get storage brain:mem list[0].q")
    check(12, "Working-memory replay", "slot 2 is reprocessed and recorded as newest", (q0[-30:], q1[-30:]),
          q0.split(": ")[-1] == q1.split(": ")[-1], "memory list before/after")


def t13():
    idle(); x = EXP["parietal"]["x"]; lever(x, -21, True); ask(QS["parietal"])
    o, f, lf = vec("o"), fired(), lit_frac("parietal")
    lever(x, -21, False)
    check(13, "Region lesion", "parietal output 0, parietal channel silent, cortex region dark", (o, f, lf),
          o[R.index("parietal")] == 0 and "parietal" not in f and lf == 0, "o score + tract head + lamps")


def t14():
    idle(); x = EXP["parietal"]["x"]; lever(x + 2, 12, True); ask(QS["parietal"])
    f, lit, s = fired(), lit_regions(), status()
    blocked = lamp_on(30)
    lever(x + 2, 12, False)
    idle(); ask(QS["parietal"])
    f2, lit2 = fired(), lit_regions()
    check(14, "Axon lesion + repair", "lesioned: computed winner parietal, region dark, BLOCKED lamp; repaired: region lit",
          (f, lit, s[-40:], blocked, f2, lit2),
          f == ["parietal"] and "parietal" not in lit and blocked and "AXON CUT" in s and lit2.get("parietal", 0) >= 0.95,
          "tract head before the gate, cortex lamps after it, status text")


def t15():
    idle(); ask(QS["parietal"]); base = vec("o")[R.index("parietal")]
    x = EXP["parietal"]["x"]; lever(x, -46, True)
    idle(); ask(QS["parietal"]); cut = vec("o")[R.index("parietal")]
    lever(x, -46, False)
    check(15, "Synapse lesion", "parietal output drops when its direct P->o synapse is cut", (base, cut), cut < base,
          "o score with and without the synapse lever")


def t16():
    x = EXP["parietal"]["x"]
    lever(x, -21, True); lever(x, -46, True); lever(x + 2, 12, True)
    cmd("function brain:ui/repair")
    states = [cmd(f"execute if block {p} lever[powered=false]") for p in
              (f"{x} -59 -21", f"{x} -59 -46", f"{x+2} -59 12")]
    idle(); ask(QS["parietal"])
    check(16, "Repair all", "all levers reset and parietal lights again", fired(),
          all("passed" in s for s in states) and fired() == ["parietal"] and lit_frac("parietal") >= 0.95, "levers + output")


def t17():
    idle(); cmd("data merge block 2 -59 %d {front_text:{messages:[\"what is seven\",\"times eight\",\"\",\"\"]}}" % CZ)
    cmd("function brain:ui/run"); time.sleep(3)
    t_a = score("#t", "brain.st")
    for _ in range(5):
        cmd("function brain:ui/run")
    t_b = score("#t", "brain.st")
    check(17, "Repeated RUN presses", "clock not restarted while computing", (t_a, t_b), t_b >= t_a, "#t before/after 5 RUNs")
    time.sleep(RUN_WAIT - 3)


def t18():
    idle(); ask(QS["occipital"], wait=6)
    cmd("function brain:ui/reset"); time.sleep(12)
    st, lit, f = score("#state", "brain.st"), lit_regions(), fired()
    ask(QS["motor"])
    check(18, "Reset mid-computation", "state READY, nothing lit, next RUN works", (st, lit, f, fired()),
          st == 0 and not lit and not f and fired() == ["motor"], "state + lamps + next run")


def t20():
    idle(); ask(QS["parietal"])
    x, h, o = vec("x"), vec("h", 16), vec("o")
    f, lit = fired(), lit_regions()
    s = status()
    check(20, "End to end", "sign -> x -> h -> o -> physical WTA -> axon -> parietal lamps", (x, o, f, lit, s),
          x[R.index("parietal")] > 0 and max(h) > 0 and f == ["parietal"] and lit.get("parietal", 0) >= 0.95
          and "Parietal" in s, "all layers + tract + cortex lamps + status")


TESTS = [(1, t1), (2, t2), (3, t3), (4, t4), (5, t5), (5, t5b), (6, t6), (7, t7), (8, t8), (9, t9), (10, t10),
         (11, t11), (12, t12), (13, t13), (14, t14), (15, t15), (16, t16), (17, t17), (18, t18), (20, t20)]

if __name__ == "__main__":
    a = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    b = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    for n, f in TESTS:
        if a <= n <= b:
            try:
                f()
            except Exception as e:
                check(n, f.__name__, "no exception", repr(e), False, "harness")
    try:
        old = json.load(open("build/test_results.json"))
    except Exception:
        old = []
    names = {x["name"] for x in RESULTS}
    keep = [r for r in old if r["name"] not in names]
    json.dump(sorted(keep + RESULTS, key=lambda r: r["n"]), open("build/test_results.json", "w"), indent=1)
