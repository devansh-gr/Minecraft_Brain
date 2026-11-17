"""Language front end: sign text -> keyword hits per region."""
import json, math
from .common import *


def emit(c):
    w, R, N, J, ri, cx, hx, hname, W, V, feeds, col, lc, kw, lever_region, lever_syn, lever_axon, lever, lamp, status, bar = (c.w, c.R, c.N, c.J, c.ri, c.cx, c.hx, c.hname, c.W, c.V, c.feeds, c.col, c.lc, c.kw, c.lever_region, c.lever_syn, c.lever_axon, c.lever, c.lamp, c.status, c.bar)
    # ---------------- language front end -> region keyword hits
    parse = ["data modify storage brain:p lines set from block %d %d %d front_text.messages" % SIGN,
             "data modify storage brain:p l set value {}"]
    parse += [f"data modify storage brain:p l.{c} set string storage brain:p lines[{n}]" for n, c in enumerate("abcd")]
    parse += ["function brain:p/join with storage brain:p l",
              'data modify storage brain:p w set value ""', 'data modify storage brain:p qn set value ""',
              "scoreboard players set #i brain.t 0",
              "execute store result score #len brain.t run data get storage brain:p q"]
    parse += [f"scoreboard players set {r} brain.s 0" for r in R]
    parse += ["function brain:p/loop"]
    w("p/parse", parse)
    w("p/join", ['$data modify storage brain:p q set value "$(a) $(b) $(c) $(d) "'])
    w("p/loop", ["execute if score #i brain.t >= #len brain.t run return 0",
                 "execute store result storage brain:p i int 1 run scoreboard players get #i brain.t",
                 "scoreboard players add #i brain.t 1",
                 "execute store result storage brain:p j int 1 run scoreboard players get #i brain.t",
                 "function brain:p/char with storage brain:p",
                 'data modify storage brain:p n set value " "',
                 "function brain:p/norm with storage brain:p",
                 'execute if data storage brain:p {n:" "} unless data storage brain:p {w:""} run function brain:p/word',
                 'execute if data storage brain:p {n:" "} run data modify storage brain:p w set value ""',
                 'execute unless data storage brain:p {n:" "} run function brain:p/app with storage brain:p',
                 "function brain:p/loop"])
    w("p/char", ["$data modify storage brain:p c set string storage brain:p q $(i) $(j)"])
    w("p/norm", ['$data modify storage brain:p n set from storage brain:lc m."$(c)"'])
    w("p/app", ['$data modify storage brain:p w set value "$(w)$(n)"'])
    w("p/qn", ['$data modify storage brain:p qn set value "$(qn)$(w) "'])
    w("p/word", ["execute store result score #ql brain.t run data get storage brain:p qn",
                 "execute if score #ql brain.t matches ..40 run function brain:p/qn with storage brain:p",
                 "data modify storage brain:p s set from storage brain:p w",
                 "execute if function brain:p/try run return 1",
                 "execute store result score #wl brain.t run data get storage brain:p w",
                 "execute if score #wl brain.t matches ..3 run return 0",
                 "data modify storage brain:p e1 set string storage brain:p w -1",
                 "data modify storage brain:p e2 set string storage brain:p w -2",
                 "data modify storage brain:p e3 set string storage brain:p w -3"] +
      [f'execute if data storage brain:p {{e{len(suf)}:"{suf}"}} if function brain:p/st_{suf} run return 1'
       for suf in ["ing", "ies", "ed", "es", "ly", "er", "s"]])
    w("p/try", ["return run function brain:p/try_m with storage brain:p"])
    w("p/try_m", ['$execute if data storage brain:kw m."$(s)" run return run function brain:p/hit with storage brain:kw m."$(s)"',
                  "return fail"])
    w("p/hit", ["$scoreboard players add $(r) brain.s 1", "return 1"])
    cut = lambda n: f"data modify storage brain:p s set string storage brain:p w 0 -{n}"
    tr = "execute if function brain:p/try run return 1"
    w("p/st_ing", [cut(3), tr, "function brain:p/add_e with storage brain:p", tr, "return fail"])
    w("p/st_ies", [cut(3), "function brain:p/add_y with storage brain:p", tr, "return fail"])
    w("p/st_ed", [cut(2), tr, cut(1), tr, "return fail"])
    for suf, n in [("es", 2), ("ly", 2), ("er", 2), ("s", 1)]:
        w(f"p/st_{suf}", [cut(n), tr, "return fail"])
    w("p/add_e", ['$data modify storage brain:p s set value "$(s)e"'])
    w("p/add_y", ['$data modify storage brain:p s set value "$(s)y"'])

