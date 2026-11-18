"""Tick-time benchmark: samples /tick query every 5 s across a whole activation and reports the worst window."""
import json, re, sys, time
from rcon import cmd
import test as T


def window():
    q = cmd("tick query")
    m = re.search(r"Average time per tick: ([\d.]+)ms.*P50: ([\d.]+)ms P95: ([\d.]+)ms P99: ([\d.]+)ms", q.replace("\n", " "))
    return tuple(float(v) for v in m.groups()) if m else None


def scenario(name, start):
    T.idle(); time.sleep(6)
    start()
    worst = None
    for _ in range(9):                    # 45 s covers stimulus -> excitation -> ladders -> decay
        time.sleep(5)
        w = window()
        if w and (worst is None or w[3] > worst[3]):
            worst = w
    print(f"{name:28s} worst 5-s window: mean {worst[0]:.1f} ms, P95 {worst[2]:.1f}, P99 {worst[3]:.1f}")
    return dict(name=name, mean=worst[0], p95=worst[2], p99=worst[3])


if __name__ == "__main__":
    res = []
    q = lambda lines: lambda: (cmd("data merge block 2 -59 -74 {front_text:{messages:%s}}" % json.dumps((lines + ["", "", "", ""])[:4])),
                               cmd("function brain:ui/run"))
    res.append(scenario("largest region (prefrontal)", q(["should i quit", "my job?"])))
    res.append(scenario("2-way tie", q(["can you hear", "and see it?"])))
    res.append(scenario("8-way tie (worst case)", lambda: cmd("function brain:dbg/inject {c0:15,c1:15,c2:15,c3:15,c4:15,c5:15,c6:15,c7:15}")))
    if "--sustained" in sys.argv:
        T.idle()
        for n in range(6):
            res.append(scenario(f"sustained run {n+1}", q(["what is seven", "times eight?"])))
    json.dump(res, open("build/perf.json", "w"), indent=1)
