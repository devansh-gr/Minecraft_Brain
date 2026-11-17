"""Ask questions over RCON and report which cortex regions lit (fraction of lamps)."""
import json, random, sys, time
from rcon import cmd

EXP = json.load(open("build/expect.json"))
random.seed(1)
SAMPLE = {r: random.sample(v["lit"], min(60, len(v["lit"]))) for r, v in EXP.items()}


def lit_frac(r):
    ok = sum("passed" in cmd(f"execute if block {x} -58 {z} redstone_lamp[lit=true]") for x, z in SAMPLE[r])
    return ok / len(SAMPLE[r])


def ask(q, wait=22):
    lines = (q + ["", "", "", ""])[:4]
    cmd("data merge block 14 -59 -26 {front_text:{messages:%s}}" % json.dumps(lines))
    cmd("function brain:read")
    time.sleep(wait)
    on = {r: lit_frac(r) for r in EXP}
    return {r: round(f, 2) for r, f in on.items() if f > 0}


if __name__ == "__main__":
    qs = [["what is seven", "times eight?"], ["What COLORS do", "you see in a", "rainbow?"],
          ["how do i keep", "my balance on", "a skateboard"], ["should i quit", "my job"],
          ["how do you say", "hello in", "spanish"], ["why does my", "back itch"],
          ["who sang that", "song yesterday"], ["how fast can", "i run a mile"], ["xyzzy"]]
    for q in qs[: int(sys.argv[1]) if len(sys.argv) > 1 else None]:
        print(" / ".join(q), "->", ask(q))
    time.sleep(16)
    print("after timeout ->", {r: round(lit_frac(r), 2) for r in EXP if lit_frac(r) > 0})
