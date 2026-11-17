# Redstone Cortex: Research Notebook

Running log of design decisions, parameters and verification results, kept as source material for the paper. Entries are dated. Numbers are copied from generator and test output, not estimated.

## 1. Objective

Build a neuroscience-inspired circuit model in vanilla Minecraft (Java 26.3, no mods) in which a typed question is routed to one of eight cortical regions through visible redstone computation, and the selected region is displayed on a cortex map reconstructed from an MRI atlas. The model is a didactic circuit analogy. It is not a biologically accurate brain simulation: real cognition is distributed, and keyword matching does not identify the regions a question actually engages.

## 2. Version history

| Version | Date | Summary |
|---|---|---|
| v1 | 2026-11-17 | 3D voxel brain (4 mm voxels, 38 x 40 x 49 blocks, 36,151 voxels), glass shell over a redstone lamp layer. Redstone winner-take-all board. Region lighting by 16 command blocks (on/off relays) that placed redstone blocks behind the lamps. Chat output for debugging. |
| v2 | 2026-11-18 | Flat lateral cortex map (1.3 mm per block, 148 x 122 cells) lit entirely by redstone dust meshes with repeater rings, so activation spreads outward as a wave. Command blocks reduced from 17 to 1 (the input button). Visible competition bars, lesion levers, stained-glass colour layer, note-block output, expanded lexicon with suffix stripping, no chat output. |

Reason for the v1 to v2 change: v1 relied on command blocks for the visual output, and powering an arbitrary 3D lamp shell with redstone alone was not tractable (dust needs an air block above it and only powers the block beneath it or the block it points into). A horizontal map allows every lamp to be powered by dust lying directly on it.

## 3. Anatomical model

- Atlas: Harvard-Oxford cortical maximum-probability atlas, threshold 0, 1 mm (`cort-maxprob-thr0-1mm`), plus the subcortical atlas (`sub-maxprob-thr0-1mm`) for the brain stem, obtained with nilearn. Brain extent from the MNI152 brain mask (resolution 1, resampled to the atlas grid with nearest-neighbour interpolation).
- Cerebellum: mask voxels with no cortical or subcortical label and voxel index z < 68 (inferior), since Harvard-Oxford has no cerebellar label.
- Projection: left hemisphere, lateral view. For each (anterior-posterior, inferior-superior) position the first in-mask voxel along +x is taken. Unlabelled surface voxels take the label up to 7 voxels deeper, then the nearest labelled voxel (Euclidean distance transform).
- Resampling: 1.3 mm per block, nearest neighbour. Final map 148 x 122 blocks, 12,856 brain cells.
- Cleanup: for each region only the largest connected component is kept; smaller fragments are reassigned to their most common neighbouring region.
- Orientation in the world: anterior to the west, superior to the north, so viewed from above with north up the map reads as a standard left lateral view.

Region grouping (Harvard-Oxford label indices):

| Region | Labels | Colour |
|---|---|---|
| Prefrontal | 1, 3, 4, 25, 27, 28, 29, 33 | light blue |
| Broca | 5, 6, 41 | purple |
| Motor | 7, 26 | red |
| Somatosensory | 17, 42 | orange |
| Parietal | 18, 19, 20, 21, 30, 31, 43 | yellow |
| Temporal | 2, 8 to 16, 34, 35, 37, 38, 44, 45, 46 | lime |
| Occipital | 22, 23, 24, 32, 36, 39, 40, 47, 48 | blue |
| Cerebellum | derived (see above) | pink |
| Brain stem | subcortical "Brain-Stem" | gray, not active |

Known simplification: emotion words map to prefrontal (orbitofrontal and anterior cingulate are included there) because limbic structures are not visible on a lateral surface.

## 4. Circuit architecture

Signal path: sign (stimulus) -> button and the single command block (transduction) -> datapack parser -> barrels (signal strength) -> comparator winner-take-all -> lamp axons -> under-map tracts -> cortex dust mesh.

### 4.1 Graded signals
A comparator reading a 27-slot barrel outputs `1 + floor(14 * fill)` for any non-empty barrel, where `fill = items / (64 * 27)`. The datapack writes the minimum item count `ceil(1728 * (s - 1) / 14)` to obtain strength s (asserted for s = 0 to 15 in the generator). Three barrels per column: inhibitory pool (level y = -60), excitatory pool (y = -59), display pool (y = -59, row z = -3).

### 4.2 Winner-take-all (lateral inhibition)
- Running maximum: comparators reading the inhibitory barrels strongly power a chain of solid blocks linked by compare-mode comparators. A block strongly powered by several comparators carries the maximum of their strengths, and comparator links do not decay, so the chain end holds M = max(A_i).
- Lift to the upper layer without decay: the chain end strongly powers a block, dust on top of that block takes the full strength, and a comparator reads that dust.
- Broadcast: a comparator chain carries M back along all columns. Spurs of three comparators deliver M to the side input of each decision comparator.
- Decision: compare-mode comparator, rear = excitatory barrel (A_i), side = M. Output is A_i if A_i >= M, else 0. Ties fire all tied regions.
- Feedforward inhibition: the inhibitory barrels are filled before the excitatory ones. If both were filled together, every column would briefly output A_i before M arrived (about 40 comparator delays), producing false spikes. Filling the excitatory pool 180 ticks later removes this transient.

### 4.3 Visible competition
The display barrel is filled with A_i at t = 0. Its decision comparator (rear A_i, side M) drives a 15-block dust line on redstone lamps, so the number of lit lamps equals the surviving strength. The inhibitory pools are filled in a ramp: at step k (every 6 ticks, k = 1 to 15) each pool is set to min(A_i, k). M therefore rises gradually, and each candidate bar goes dark once M exceeds its strength, in order from weakest to strongest. The winner's bar remains.

### 4.4 Axons
- Each decision output drives a delay-1 repeater (all-or-none conversion to strength 15, analogous to the axon hillock).
- The tract is dust on redstone lamps (the lamps show the signal travelling), with delay-4 repeaters every 7 blocks (analogous to nodes of Ranvier restoring signal that dust loses at 1 per block).
- A branch at z = 6 powers a note block (one instrument and pitch per region).
- Routing: board columns are ordered by the x coordinate of their region's feed point. Tracts turning west turn in increasing z order from the leftmost column; tracts turning east are mirrored. This ordering makes the fan-out planar (no crossings), so no tract touches another.
- Under the map, tracts run at y = -59 beneath the lamp layer. The final repeater strongly powers a stone block; dust on top of it (in a hole in the lamp layer, y = -58) climbs onto the mesh above at strength 14.

### 4.5 Cortex dust mesh
Per region:
1. Boundary cells (any 4-neighbour outside the region) receive region-coloured concrete and no dust. This keeps region networks electrically separate and draws the region outlines.
2. Feed cell: interior cell with the largest taxicab distance to the boundary.
3. Taxicab BFS distance d from the feed over the remaining cells.
4. Cut cells: d divisible by 6 (RING = 5 dust cells between rings). Cut cells are concrete without dust, so zones are only connected through repeaters and cannot latch themselves on.
5. Repeaters (delay 2) are placed on cut cells whose rear neighbour has distance d - 1 and front neighbour d + 1 on the same axis, with no two repeaters adjacent (prevents side locking).
6. A Python simulation of dust power (decay 1 per block, repeaters restore 15) checks coverage before building.

| Region | Cells | Dust | Repeaters | Rings | Simulated coverage |
|---|---|---|---|---|---|
| Prefrontal | 3079 | 2309 | 442 | 19 | 100% |
| Broca | 399 | 253 | 48 | 3 | 99% |
| Motor | 807 | 500 | 87 | 13 | 100% |
| Somatosensory | 924 | 615 | 110 | 11 | 100% |
| Parietal | 1029 | 672 | 117 | 6 | 100% |
| Temporal | 2941 | 2231 | 420 | 12 | 100% |
| Occipital | 2360 | 1759 | 336 | 9 | 100% |
| Cerebellum | 990 | 726 | 138 | 6 | 100% |
| Total | 12,529 | 9,065 | 1,698 | | 99.9% |

A stained-glass layer in each region's colour sits above the dust (y = -56). Glass is not a redstone conductor, so it does not alter dust connections.

### 4.6 Lesions
Each column has a floor lever and a warning lamp. A pulled lever silences that region: the parser sets its score to 0 before signals are computed, so the region drops out of the competition and the runner-up wins. This is implemented in the datapack, not in redstone. A purely redstone lesion at the barrel comparator was considered and rejected, because the only free side positions are adjacent to the max-chain comparators of the neighbouring column, and powering them would corrupt the global maximum.

## 5. Language front end (datapack)

- Input: the four lines of the sign are read with `data get block ... front_text.messages` (plain strings in 26.3) and joined with spaces.
- Tokenisation: a recursive function slices one character at a time (`data modify ... set string ... i j`). A storage lookup lowercases letters, maps digits to `#` (so any number becomes a numeric token), drops apostrophes and treats everything else as a separator.
- Lookup: exact match in an 863-word lexicon (`lexicon.py`). On a miss, one suffix is stripped and the stem retried: -ing (also -ing to -e), -ies to -y, -ed (also -d), -es, -ly, -er, -s.
- Scoring: h = keyword hits per region. Signal s = min(15, 2h + 1) for h > 0, else 0. If no region scores, temporal receives s = 1 (fallback: comprehension only).
- Only the sign reader, the barrel filling and the timing schedule use commands. One command block (on the button) starts the parser.

## 6. Timing (game ticks, 20 per second)

| t | Event |
|---|---|
| 0 | Button pressed: parse, display barrels filled, candidate bars appear |
| 20 to 104 | Inhibitory ramp, 15 steps of 6 ticks |
| about 104 to 190 | M propagates through the comparator chain; losing bars go dark |
| 200 | Excitatory barrels filled; winner fires |
| 200 to about 260 | Spike travels the lamp axon and the under-map tract |
| about 260 to 340 | Ring-by-ring wave across the region (up to 19 rings x 4 ticks) |
| 460 | All pools cleared; activity decays in the same ring order |

## 7. Verification

Method: dedicated 26.3 server, RCON client (`rcon.py`), automated script (`test.py`). For each question the sign text is written, the parser is run, and after 22 seconds 60 random lamps per region (from the generator's expected-lit list) are tested with `execute if block ... redstone_lamp[lit=true]`.

Results (2026-11-18, v2):

| Question | Lit (fraction of sampled lamps) |
|---|---|
| what is seven times eight? | parietal 1.0 |
| What COLORS do you see in a rainbow? | occipital 1.0 |
| how do i keep my balance on a skateboard | cerebellum 1.0 |
| should i quit my job | prefrontal 1.0 |
| how do you say hello in spanish | broca 1.0 |
| why does my back itch | prefrontal 1.0, somatosensory 1.0 (tie) |
| who sang that song yesterday | temporal 1.0 |
| how fast can i run a mile | motor 1.0 |
| xyzzy | temporal 1.0 (fallback) |
| (after timeout) | none |

Competition time series, question "what color is the sky when i feel sad and hear music?" (display comparator outputs, ramp at 4 ticks per step during this run):

| t (s) | Surviving candidates |
|---|---|
| 1 | prefrontal 3, somatosensory 3, temporal 7, occipital 5 |
| 4 | temporal 7 |
| 10 | temporal 7 |

Lesion experiment, question "what song do you hear when you see red":

| Condition | Lit |
|---|---|
| intact | temporal 1.0 |
| temporal lesioned | occipital 1.0 (runner-up); lesion lamp on |

v1 results (2026-11-17, superseded): the same parser with 4 mm voxel brain; 6 of 6 test questions correct, ties lit both regions, timeout cleared.

## 8. Engineering issues encountered

1. Servers since 1.21.2 pause ticking when no player is online (`pause-when-empty-seconds`, default 60). Comparators stopped updating during automated tests. Fixed with `pause-when-empty-seconds=-1`.
2. `execute if function` cannot pass macro arguments; wrapped with a non-macro function that does `return run function ... with storage`.
3. `setworldspawn` and the daylight gamerule changed syntax in 26.x (`advance_time`); spawn was written to `level.dat` with nbtlib instead.
4. Repeaters are locked by diodes pointing into their sides, so mesh repeaters are never placed adjacent to each other.

## 9. Limitations

- Keyword matching, not comprehension. Example: "how do I quit soccer" routes to motor.
- Strict winner-take-all is a simplification; real cortical activity is distributed and graded.
- Left hemisphere only; medial and limbic regions are not shown.
- Cerebellum boundary is a heuristic (Section 3).
- Lesions are applied in the datapack, not by severing redstone.
- Not tested in the game client by the author's tooling; verification was on a dedicated server.

## 10. Reproduction

```
python3 -m venv .venv && .venv/bin/pip install numpy scipy nibabel nilearn nbtlib
.venv/bin/python gen.py            # writes build/datapack/redstone_cortex
# copy the datapack into a flat 26.3 world, then in game or over RCON:
/forceload add -64 -34 96 172
/function brain:build
```

---

## 11. Version 3 (2026-11-18): network, memory, plasticity, lesions, laboratory

### 11.1 Phase 0: audit and backup
Backups: `backups/world-v2-20261117-1506.tgz` (server world) and `backups/saves-Brain-v2-20261117-1506.tgz` (client save); git tag `v2`. Audit result: every v2 subsystem (parser, barrel encoding, comparator WTA, tracts, cortex meshes, lever lesions) had passed its tests and was retained. v3 was applied to the existing world rather than a regenerated one.

### 11.2 Network (datapack, integer arithmetic)
- Inputs: x_i = min(15, 3 n_i), where n_i is the keyword count for category i.
- Hidden layer, 16 units: 8 primary units P_i with W(i -> P_i) = 4, and 8 association units A_m with W = 2 from each of a region pair: (prefrontal, temporal), (Broca, temporal), (motor, cerebellum), (motor, somatosensory), (somatosensory, parietal), (parietal, occipital), (temporal, occipital), (prefrontal, parietal). Biases 0.
- Hidden dynamics, 4 steps (game ticks 12, 24, 36, 48): I = floor(sum_j u_j / 16); d_j = clamp(floor((sum_i W_ij x_i + b_j) / 4) - I, 0, 15); u_j <- u_j + floor((d_j - u_j + 1) / 2); h_j = u_j. u starts at 0 for each run. This is a first-order leaky integrator with ceiling rounding and a global subtractive inhibitory feedback term.
- Outputs: o_k = clamp(floor((sum_j V_jk h_j + c_k) / 4), 0, 15). Baseline V(P_k -> o_k) = 4, V(A_m -> o_a) = V(A_m -> o_b) = 1, all others 0; c_k = 0. The output range 0 to 15 maps directly to comparator signal strength.
- Overflow bound: |sum| <= 16 x 15 x 12 = 2,880, far inside the 32-bit scoreboard range.
- Hand calculation check: "can you hear and see it" gives x_temporal = x_occipital = 3, h(P) = 3, h(A temporal+occipital) = 3, o_temporal = o_occipital = 4. Measured values matched exactly.

### 11.3 Plasticity
TRAIN with a selected target t and the LEARN lever on: for each hidden unit with h_j > 0, delta = ceil(h_j / 4); V_jt += delta (capped at 12); for every k != t with o_k >= o_t and o_k > 0, V_jk -= delta (floored at -8). Input-to-hidden weights W are fixed. Weights live in the scoreboard objective `brain.w`, which is saved with the world. `brain:load` re-initialises weights only if `#init` is unset, so `/reload` and restarts keep learned values. RESET LEARNING restores the baseline listed above.
Measured: one TRAIN toward occipital after the tied run above changed 12 synapses (6 up, 6 down) and the rerun produced o_temporal = 1, o_occipital = 7, a single Visual winner.

### 11.4 Working memory
Five most recent runs in `storage brain:mem list`: normalised text, x[8], o[8], winner string (from the physical readout), lesion flag, trained flag. REPLAY n loads x from record n and reruns from the input stage with the current weights.

### 11.5 Lesions
| Type | Control | Mechanism | Effect |
|---|---|---|---|
| Region | lever at (x, -59, -21) | datapack sets u(P_k) = 0 each step and o_k = 0 | region leaves the competition; runner-up can win |
| Synapse | lever at (x, -59, -46) | datapack subtracts V(P_k -> o_k) h(P_k) | output drops; association paths remain |
| Axon | lever at (x+2, -59, 12) | lever -> dust on glass -> side of a subtract-mode comparator in the tract: output 15 - 15 = 0 | decision fires, cortex region stays dark |

Measured: synapse lesion on parietal lowered o_parietal from 10 to 2; three TRAIN updates toward parietal under the lesion raised it to 9 (recovery through association units). Training also increments the lesioned synapse; that increment has no effect until the lesion is repaired.

### 11.6 State machine and console
A tick function runs a clock while a computation is active and polls every console button for a rising edge (no command blocks remain in the world). Stages: input (t = 1), hidden steps (12, 24, 36, 48), output (60), inhibitory ramp (76 to 160, every 6 ticks), excitation (250), readout (380), decay (560), idle (580). RUN is ignored while computing. RESET clears barrels and returns to READY. The readout records which tract heads fired (physical decision) and whether each winner's cortex feed is powered (delivery).

### 11.7 Laboratory
Polished deepslate floor, blackstone-brick perimeter walls with tinted-glass bands, deepslate-tile pillars with sea-lantern cores, black stained-glass roof, a blackstone and oxidised-copper plinth around the cortex, an observation balcony at y = -47 north of the cortex, zone titles and a region legend as text displays. Cortex changes: ring cut cells are now lamps (removing the diamond pattern in the idle state); region borders carry a second layer of stained glass (raised sulci). Seven camera presets (`brain:cam/*`).

### 11.8 Verification and performance
See `TEST_REPORT.md`: 21 of 21 checks passed. One defect was found and fixed (axon lever did not drive the gate comparator because levers give direct power only to their attached block). Tick time during a full run: mean 1.0 ms, P99 3.9 ms.

### 11.9 Not verified
Visual appearance and camera framing were not inspected in a game client.

## 12. Phase 1 validation (2026-11-18)
Full record in `PHASE1_EVIDENCE.md`. Summary:
- Code structure: `net.py` was split into the `dp/` package (13 modules, one per subsystem). The generated datapack is byte-identical before and after (137 files).
- Test copy of the installed world loaded the datapack with zero errors; a planted invalid function was reported, confirming that the log check works.
- Forward pass: two inputs gave different hidden and output activations, identical to an independent reference implementation (`reference.py`) fed the in-game weights, including after four weights were altered inside the game only.
- Integration: comparator readings equal the datapack outputs on all 8 channels; the max chain carries the maximum; only the maximal channel's decision comparator outputs.
- Causality: removing one inhibition comparator made a non-maximal channel fire with unchanged datapack values. Runtime functions write only barrels, console indicator bases and lever states.
- Stated limitation: input-to-hidden connectivity is sparse (24 fixed synapses); only hidden-to-output (128 synapses) is dense and plastic.

## 13. Follow-up validation and Phase 2 (2026-11-18)
- Hidden updates are synchronous by construction (section 8.1 of `PHASE1_EVIDENCE.md`).
- Bounds hold for every weight configuration the plasticity rule permits; the +12 and -8 caps were reached and held in game (8.2).
- Physical WTA: 25 of 25 vectors, including all one-hot cases, ties of 2, 3 and 8, and all-zero (8.3).
- In-client: a real player press on RUN started computation; the parietal cortex visibly lit. Camera presets and overall lighting were found deficient (8.4).
- Phase 2 (`PHASE2_EVIDENCE.md`): "what color is the sky when i feel sad and hear music?" was physically classified as temporal (o = 10 vs occipital 5). One TRAIN toward the measured runner-up (occipital) changed 22 hidden-to-output synapses. The rerun was physically classified as occipital (15 vs 0). After a server restart the weights were identical and the classification was unchanged.
- Phase 3 (`PHASE3_EVIDENCE.md`): on the same input, an axon cut preserved computation and the physical decision but blocked cortex delivery; repair restored it. A region lesion made the runner-up win. A synapse lesion dropped the winner from 10 to 3; one TRAIN under the lesion restored it through association synapses.
