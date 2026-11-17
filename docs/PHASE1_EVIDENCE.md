# Phase 1 Evidence: Forward Pass and Redstone Integration

Run on 2026-11-18 on a test copy of the installed world (`server/BrainTest`, copied from `saves/Brain`), Minecraft 26.3 dedicated server. Scripts: `validate_phase1.py` (raw output in `build/phase1.json`), `reference.py`.

## 0. Modularity check
`net.py` (one file, 11 subsystems) was split into the package `dp/` with one module per subsystem: `common`, `barrels`, `persist`, `parser`, `network`, `pipeline`, `inject`, `memory`, `plasticity`, `experiments`, `debug`, `control`, `console`. The split was verified behaviour-preserving: all 137 generated datapack files are byte-identical before and after (`diff -r` empty).

## 1. The forward pass as generated
Source: `dp/network.py`. Output: `data/brain/function/net/hidden_step.mcfunction` (261 commands, run 4 times per question) and `net/output.mcfunction` (433 commands).

| Quantity | Definition |
|---|---|
| Input | x_i = min(15, 3 n_i), n_i = keyword hits in category i |
| Input -> hidden | sparse and fixed: W(i -> P_i) = 4 (8 synapses), W(a -> A_m) = W(b -> A_m) = 2 (16 synapses); biases b_j = 0 |
| Hidden update (4 steps) | I = floor(sum_j u_j / 16); d_j = clamp(floor(sum_i W_ij x_i + b_j) / 4) - I, 0, 15); u_j += floor((d_j - u_j + 1) / 2); h_j = u_j |
| Hidden -> output | dense and plastic: 16 x 8 = 128 synapses V_jk; baseline V(P_k -> o_k) = 4, V(A_m -> o_a) = V(A_m -> o_b) = 1, others 0; c_k = 0 |
| Output | o_k = clamp(floor((sum_j V_jk h_j + c_k) / 4), 0, 15) |
| Activation | clamp to [0, 15] (rectified, saturating); 15 is the maximum comparator signal strength |
| Overflow bound | worst case |sum| = 16 x 15 x 12 = 2,880, far inside the 32-bit scoreboard range |

Generated code for one hidden unit (unit 12, association unit somatosensory + parietal), one step:
```mcfunction
scoreboard players operation #d brain.t = b12 brain.w
scoreboard players operation #m brain.t = W3_12 brain.w
scoreboard players operation #m brain.t *= x3 brain.n
scoreboard players operation #d brain.t += #m brain.t
scoreboard players operation #m brain.t = W4_12 brain.w
scoreboard players operation #m brain.t *= x4 brain.n
scoreboard players operation #d brain.t += #m brain.t
scoreboard players operation #d brain.t /= #hd brain.t
scoreboard players operation #d brain.t -= #I brain.t
execute if score #d brain.t matches ..-1 run scoreboard players set #d brain.t 0
execute if score #d brain.t matches 16.. run scoreboard players set #d brain.t 15
scoreboard players operation #d brain.t -= u12 brain.n
scoreboard players add #d brain.t 1
scoreboard players operation #d brain.t /= #2 brain.t
scoreboard players operation u12 brain.n += #d brain.t
```
Generated code for output 4 (parietal): 16 multiply-accumulate triples of the form
```mcfunction
scoreboard players operation #m brain.t = V0_4 brain.w
scoreboard players operation #m brain.t *= h0 brain.n
scoreboard players operation o4 brain.n += #m brain.t
```
followed by the synapse-lesion correction, the division by 4, the clamp, and the region-lesion override.

Design limitation stated plainly: only the 24 baseline input-to-hidden synapses are generated. Setting any other W in game has no effect. The hidden-to-output matrix is dense.

## 2 and 3. Two inputs, computed in game, checked against an independent reference
The values below are read back from the game's scoreboards after the output stage. `reference.py` is a separate implementation written from the equations. It is given the in-game x and the in-game weights, which are read back over RCON.

| | Q1 "what is seven times eight?" | Q2 "can you hear and see it?" |
|---|---|---|
| x (game) | [0,0,0,0,9,0,0,0] | [0,0,0,0,0,3,3,0] |
| h (game) | [0,0,0,0,8,0,0,0,0,0,0,0,3,3,0,3] | [0,0,0,0,0,3,3,0,1,1,0,0,0,1,3,0] |
| h (reference) | identical | identical |
| o (game) | [0,0,0,0,10,0,0,0] | [0,0,0,0,0,4,4,0] |
| o (reference) | identical | identical |

Proof that the game, not Python, executes the network: four weights were changed inside the game only (`W5_14=7, V14_6=9, V5_5=-3, b13=6`) and Q2 was run again. The game produced h = [0,0,0,0,0,3,3,0,1,1,0,0,0,3,5,0] and o = [0,0,0,0,0,0,15,0]. The reference matched only after reading those weights back from the scoreboard. The generator never saw these values. Weights were then reset to baseline.

## 4. Datapack loads in the test copy
- `datapack list`: `[vanilla (built-in)], [file/redstone_cortex (world)]`.
- Server log on load and on `/reload`: 0 lines containing "error" or "fail".
- Control: a deliberately invalid function (`zz_broken`) was added and reloaded. The log printed `ERROR: Failed to load function brain:zz_broken`. After removing it and reloading, the error count was 0 again. So a clean log does mean every function loaded.

## 5. In-game input reaches the physical circuit
The sign was set to "what is seven times eight?" and the RUN button was placed in its pressed state. The datapack tick poller detected it, with no direct function call. Readings at game tick 300:

| | prefrontal | Broca | motor | somato | parietal | temporal | occipital | cerebellum |
|---|---|---|---|---|---|---|---|---|
| datapack o | 0 | 0 | 0 | 0 | 10 | 0 | 0 | 0 |
| inhibitory barrel comparators | 0 | 0 | 0 | 0 | 10 | 0 | 0 | 0 |
| decision comparators | 0 | 0 | 0 | 0 | 10 | 0 | 0 | 0 |

Max-chain end M = 10. Tract head fired: parietal.

With all eight channels carrying different values (injected vector [2,5,11,4,7,3,1,6], physical channel order prefrontal, Broca, motor, temporal, somato, parietal, cerebellum, occipital):

| | ch1 | ch2 | ch3 | ch4 | ch5 | ch6 | ch7 | ch8 |
|---|---|---|---|---|---|---|---|---|
| inhibitory comparators | 2 | 5 | 11 | 4 | 7 | 3 | 1 | 6 |
| decision comparators | 0 | 0 | 11 | 0 | 0 | 0 | 0 | 0 |

M = 11. Fired: channel 3 (motor) only.

## 6. The physical comparators decide
**Hardware tamper test.** The same injected vector was used, so the datapack values were identical in every condition. Only one block in the circuit was changed: the comparator that delivers M to channel 5's decision input.

| Condition | Channels fired |
|---|---|
| Circuit intact | motor |
| Channel 5's inhibition comparator removed | motor and somatosensory |
| Comparator replaced | motor |

With its inhibition input gone, channel 5 (value 7, not the maximum) fired. The datapack had not changed, so the winner is set by the hardware. Note: in the tampered run the status text was read mid-run ("COMPUTING · winner fires down its axon"), because the check ran at 16 s and the readout happens at 19 s.

**Static audit.** These are all the block-writing commands in the 127 runtime functions (the build functions excluded):

| Command | Count | Target |
|---|---|---|
| `item replace ... container.N` | 432 | the 40 barrels (filling and clearing) |
| `setblock ... polished_blackstone` / `redstone_block` | 166 | indicator-lamp bases on the console desks (z = -70 and z = -79) |
| `setblock ... lever` | 27 | REPAIR and experiment presets resetting or setting lesion levers (z = -21, -46, 12) and the LEARN lever |

No runtime command writes a comparator, repeater, dust, tract block or cortex lamp. The readout only reads block states (`execute if block`) to report the outcome.

## 7. Executed vs unverified
Executed with the outputs above: modular split identity, datapack load with the negative control, two-input forward pass against the reference, in-game weight perturbation, physical button to comparator readings, 8-channel comparator readings, hardware tamper test, static audit. Earlier full suite: 21 of 21 checks (`TEST_REPORT.md`).

Not verified:
- Visual appearance in a game client (all tests ran on a headless server).
- A click by a real player: the button was set to its pressed state with `setblock`, which the poller treats the same way.
- Behaviour on Lunar Client specifically: it runs the same vanilla 26.3 server logic in singleplayer, but this was not observed.
