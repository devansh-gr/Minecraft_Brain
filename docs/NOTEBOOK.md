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

## 14. Visual round 1 (2026-11-18), verified in client
- First in-client screenshots showed: camera presets dropping the player (creative gravity), the reveal blocked by the balcony, diamond ring patterns, a dark scene, and rain.
- Changes: camera presets use spectator mode; the cortex rings follow Euclidean distance, so they appear as circular ripples (946 repeaters, down from 1,698; simulated coverage 99.8%); invisible light blocks (level 6) on a 7-block grid above the cortex; balcony removed; weather fixed clear (`advance_weather false`); labels on all 16 hidden neurons.
- Region beams: each region has a beacon under its cortex. A sticky piston holds a shutter block in the beam column; it is powered by a redstone torch mounted on the region's feed block. When the region's spike arrives, the feed block is powered, the torch turns off, the piston retracts and a beam in the region's glass colour rises through the roof. This is pure redstone; no command drives it. Bug found: piston quasi-connectivity kept the shutter closed (fixed, see `TEST_REPORT.md`).
- Regression after these changes: 21 of 21 checks.
- Remaining visual weakness, stated plainly: the lab is large and dim between zones, beams are thin at a distance, and the cortex is still a flat relief.

## 15. Visual round 2 (2026-11-18), verified in client
- Neurons: 8 input and 16 hidden neurons are 16-step lamp staircases rising toward the console. Step 0 is a plain block because each dust step also powers the next step's block; with that offset, lit lamps = activation exactly (verified on two inputs, all 24 neurons).
- 3D brain. A genuinely volumetric lamp brain cannot be lit by redstone without command blocks (v1 finding). The cortex is therefore a relief whose height at each cell is the lateral bulge of the real 3D cortical surface (MNI depth of the first in-brain voxel along x), scaled by 0.45 and capped at 16 blocks, then projected so that 4-neighbours differ by at most 1 (dust can climb one block). Mean height 12 blocks.
- Feeds on the relief: each region's entry block sits on a torch ladder (block, torch, block, ...). Feed heights are multiples of 4 so the top block is powered exactly when the tract is; feed neighbours are capped at the feed height.
- Slope repeaters: a repeater works if its back cell is level or one higher (it reads that cell's dust-powered lamp) and its front is level or one higher (it strongly powers that lamp, which powers its dust). For a front one lower, the lower cell's glass slot holds a lamp that the repeater powers and that powers the dust beneath it; such capped cells lose their uphill dust links, which the coverage simulation models. Coverage went from 91.7% (flat-only repeaters) to 99.8%.
- Beam banks: 3 beacons per region (24 in total). Torch on the feed block -> dust line -> branches -> sticky pistons holding shutter blocks in the beam columns. Verified: 0 open at idle, 3 for a single winner, 6 for a tie, 0 after decay.
- Look: bare lamps (no tinted glass over the interior) for contrast, with coloured glass only on borders and beam columns; lit walkway, zone outlines, brain halo, wall light bands, ambient light outside the brain footprint; roof at y = 0.
- Regression: 21 of 21 after fixing two regressions caused by the round (see `TEST_REPORT.md`, items 4 and 5). Tick time: mean 1.4 ms, P99 3.9 ms.

## 16. Upright volumetric brain (2026-11-18), prototype world `BrainUpright`
- Design change requested: a giant, upright, genuinely 3D brain with its left lateral profile facing the entrance. The v3.2 relief world stays installed unchanged; the upright build lives in a separate prototype world and behind `MODE = "upright"` in `gen.py` (`"relief"` restores v3.2).
- Geometry (`upright.py`): MNI152 grey + white matter templates (sum > 0.5, intersected with the brain mask) so sulci are carved by CSF; Harvard-Oxford labels; both hemispheres, cerebellum and brainstem. 1.5 mm per block: 519,814 voxels, bounding box 120 x 106 x 96 blocks. Orientation: MNI x -> world z (left hemisphere faces north), MNI y -> world x (frontal lobe east), MNI z -> world y.
- Shell: outer voxels are region-coloured stained glass, the next layer black concrete; invisible level-8 light blocks two blocks outside the surface light the glass.
- Lighting circuit per region (left hemisphere): one torch ladder rising from the region's axon. Blocks at 4-level intervals are powered exactly while the axon is. At those levels a horizontal dust-on-lamp plate fills a band up to 4 cells behind the surface, joined to the ladder by four straight spokes, with Euclidean repeater rings every 6 cells. A lamp under dust is strongly powered and lights adjacent lamps, so surface voxels next to a powered plate lamp are lamps too: they form visible stripes on the lobe.
- Isolation rules learned the hard way: plate cells may not border another region in their slice (neighbouring plates merged and latched); halo light blocks and stripes are kept away from ladder columns (a light block replaced a ladder torch; a stripe touched an idle-powered ladder block); the tract layer under the brain is cleared before rebuilding (stale tracts from an earlier ladder layout powered a new one); clears are sliced below the 1,000,000-block fill limit.
- Timing: ladders up to 48 torches add about 5 s, so the readout moved to 28 s and decay to 38 s.
- Performance: full-interior plates (42,708 dust) peaked at P99 76 ms when the largest region lit. Band plates (26,305 dust) and tighter rings: P99 41 ms (prefrontal) and 45 ms (temporal), mean 5 ms, within the 50 ms budget.
- In-client screenshots (`img/upright/`): front, three-quarter and side, idle and activated. Activation is visible as bright stripes across the lobe.
- 2026-11-18 (later): performance pass and upright regression, see `TEST_REPORT_UPRIGHT.md`. 21 of 21 checks; single-region P99 23 to 31 ms, ties up to 65 ms in the worst run, sustained runs at most 26 ms. Client screenshots deferred until GUI automation is approved.
- 2026-11-21: stilts and tie performance. Hidden feeds: prefrontal, Broca, somatosensory and motor now rise in short risers under the posterior brain and cross inside it on dust-on-glass lines; exposed ladders went from 19 to 29 blocks down to 4 to 8, with temporal left at 14 (21 percent plate loss if hidden). Cost: the lowest plates of prefrontal (17 percent of lit lamps) and Broca (22 percent). Performance: tinted-glass interior seal, axon stagger of 5 redstone ticks per column (ties cascade over 1.75 s; finer stagger cannot help because plates repeat every 2 redstone ticks), dropped items killed after builds. P99 at or below 27.7 ms in all 11 windows, including 8-way ties. Regression 21 of 21 including restart. Details: `TEST_REPORT_UPRIGHT.md`.
- 2026-11-21 (later): review fixes. Build cleanup limited to Age-0 items inside the build's own box (the global item kill is gone); build stops changing random ticks, weather and command-block output world-wide. In-game anatomy sweep: 14,835 of 14,835 expected lamps lit, 0 of 8,400 foreign lamps; losses vs `2d30a70`: prefrontal -17.1%, Broca -22.2%, temporal -3.5%, parietal -0.1%. Suite 20/20, WTA 25/25, P99 at most 27.8 ms with default gamerules.
- 2026-11-21 (final safety pass): Age-0 drop cleanup cannot prove an item came from the build, so it is opt-in (`#drop_cleanup`, test world only). `brain:build` refuses unless `#build_ok` is set; `install.py` requires a fresh backup and `--yes`. Suite 20/20, WTA 25/25, restart passed earlier the same day (not rerun after the build-only changes).

### 2026-11-21: Client visual review (BrainU, test copy)
- Client 26.3, window 1500x844 points on a Retina display, captured and resampled to 1920x1080. Night was fixed with `advance_time false` in the client copy only. Ten images are in `build/visual_review` (01-04 idle, 05-08 single region from example e3, 09-10 eight-way inject).
- FPS (F3, vsync fifo, 120 Hz cap): reveal idle 117; single-region run at 10/20/30/36 s: 119/115/120/120; eight-way run: 120/110/120/120. The cap hides headroom; the minimum was 110.
- Visual defects, by severity: (1) activation reads as sparse orange lamp stripes on the coloured cortex and is hard to see at reveal and wide distance; (2) the support stand reads as a tree trunk under the brain; (3) the right hemisphere never lights (decorative), which is visible from the side and front; (4) with daylight on, the lamps wash out, so a world that advances time needs night locked for display.
- No code changed.

### 2026-11-22: Visual round 3, client before/after (BrainU, test copy)
- Build f349b18 (second lamp layer, LINE=1, glass stand, halo 5). Same cameras and night setting as round 2. Images in `img/visual_round3/` (01-12, 1920x1080); `compare_idle/single/multi.jpg` put round 2 on the left and round 3 on the right.
- Better: in the three-quarter, side and front views, the lit regions show a dense lamp field instead of thin stripes. On an eight-way tie the whole left cortex reads as lit. The glass stand removes most of the tree-trunk look.
- Not fixed: (1) at the wide camera, the brain covers about 10% of the frame, so activation barely reads. (2) A single-region win on the far side (e3, parietal) is hidden from the front reveal. (3) The right hemisphere stays dark: the 11_side_ground_multi image shows one lit half. (4) Halo 5 makes the idle brain darker than in round 2.
- FPS (F3, 120 Hz vsync cap): idle 120/120; 8-way at 10/20/30 s 119/115/120; single 120/120/119. Server tick cost is unchanged from the server runs: P99 31 ms single, 51 ms on an 8-way tie.

### 2026-11-22: Visual round 4 (camera first, tick budget), server-verified, no client screenshots yet
- Rollback baseline tagged `baseline-28ms` (5d4e4cb).
- Camera: an offline z-buffer render of the build's voxels scored candidate framings by brain share of frame, lit share for one region, and board in frame. New `1_reveal` (-60, -44, 30, yaw -45, pitch -13.6): rear three-quarter, whole brain plus part of the board. The old reveal is kept as `12_front_ground`. The default sign question is now the occipital one ("what colors are in a rainbow?"). In the offline render it lights 4.0% of the frame from the new camera; the old default (parietal) lit 0.3% from the old camera.
- Tick budget: the extra cost came mostly from timing, not dust count. LINE=2 with the full mid layer is only 13.8k dust (baseline 10.6k), yet its 2-way tie stayed at 46-48 ms because each mid layer switched in the same tick as its plate. MID_DELAY=4 on the mid feed repeater splits them. Two runs: prefrontal 15.8/30.1 ms, 2-way 35.3/34.6, 8-way 35.8/33.2 (P99, worst 5-s window). Target <40 met.
- MID_EFF filter added (keep a mid layer only if lamps right behind the shell / dust >= threshold); left at 0 with LINE=2. With LINE=1 it cut dust from 38.3k to 28.4k at no visible loss, but P99 stayed at 45-57.
- Verification on the rebuilt test world: anatomy ALL OK (27,655 expected lamps, 0 foreign); suite 20/20; WTA 25/25.
- Not done: client screenshots of round 4, and localized idle lighting (needs screenshots to judge).

## 17. Hardware pivot: redstone does the arithmetic (2026-11-22, started)
Goal: the forward pass (weighted products, sums, activation, inhibition) computed by physical redstone; the datapack only sets inputs and reads outputs. Developed on a separate flat test server (`server_hw/`, RCON 25597), so the brain world is untouched.

- `hw/nor.py`: compiler from a NOR-gate netlist to redstone. Gate = stone block + wall torch (NOR of everything on its input lane). Every signal is a floor dust column; inputs branch off through a repeater (diode) and a stone step onto a lane of dust on glass two blocks up, which crosses the other columns without touching them. `Net` builds netlists with constant folding; `simulate` evaluates them in Python.
- Primitives probed in game: repeater on glass, dust climbing onto glass, crossing isolation in both directions, wall-torch NOR. All behaved as assumed.
- Full adder (9 NOR, 510 blocks): 8/8 input combinations correct in game, first build.
- 2-4-2 network as a netlist (`hw/net242.py`, same equations as reference.py; weights 5-bit signed, biases 6-bit signed, lesion levers): 9,765 NOR gates, 0/3,000 mismatches against the reference in Python simulation, with random negative weights, biases and lesions.
- Size problem: the crossbar layout costs one column per live signal and 8 rows per logic level. For the unrolled 2-4-2 (depth 353, up to 360 live signals) that is about 2,800 x 1,400 blocks, so not buildable. A lever-weighted 4-bit x 5-bit signed multiplier (337 gates) already spans 151 x 1,629 blocks, and its slowest signal takes over 45 s to arrive.
- Torch burnout: a build left some torches burned out (the torch is unlit while its block is unpowered). `rs.place` now places torches last, after the circuit settles, and `rs.relight` re-places them.
- Fresh rebuild on a properly cleared area (the earlier clear exceeded the fill volume limit, so leftover probe blocks sat inside the circuit): the physical multiplier (4-bit x times 5-bit signed lever weight, 337 NOR, 66,238 blocks, 151 x 1,629) gave 12/12 correct products in game, including -240, -156, -1 and 225. The correct value stabilised 22 to 29 s after the inputs changed. The datapack only placed input blocks and read dust power.
- Comparator XOR cell (`hw/cells.py`): two subtract-mode comparators, inputs on separate layers (floor and glass) so they cross for free. 48 blocks, 4/4 in game, no torches (no burnout). About 6x smaller than the 5-NOR torch XOR.
- Next: a full adder from two comparator XORs plus a comparator mux carry (cout = p ? c : a, with NOT p = 15 - p from a comparator on a redstone block); a small 2-layer router so cells can be wired without hand-placing; then a time-multiplexed MAC (one multiplier, one accumulator, lever weight banks, hidden-state registers) that runs the 2-4-2 and scales to 8-16-8 by adding memory, not arithmetic.

### 17.x Comparator full adder (2026-11-22)
- hw/cells.py fa_cell(): two comparator XOR cells plus a comparator carry mux (NP = 15 - p, K = c - NP, G = a - p, cout = K | G).
- 235 blocks after the fix (233 before), 23 x 19 footprint, no torches (no burnout). The torch NOR full adder was 9 gates in a crossbar band.
- In game on the HW server: 8/8 input combinations correct (hw/test_fa_cmp.py). First run was 4/8: one missing dust at the XOR2 b feed, so c never reached the sum path.

### 17.y Review 463baaf fixes (2026-11-22)
- hw/nor.py compile() referenced an undefined `level` (copy of the compile2 line): NameError on every compile() call, so test_fa.py was broken. Line removed.
- hw/test_offline.py: server-free regression (compile, compile2, FA netlist simulation, cell block counts). It reproduced the NameError before the fix and passes after.
- All hardware tests now exit nonzero on any wrong output (test_fa, test_fa_cmp, test_xor, test_mul, net242).
- The unrolled 9,765-gate 2-4-2 is frozen as a netlist reference only. Next milestone: one reusable physical MAC.

### 17.z Offline redstone simulator (2026-11-22)
- hw/rsim.py: redstone-tick simulator for the hw block subset (dust with step up/down rules, repeaters with delay and locking, subtract/compare comparators, redstone blocks, stone as conductor, glass as non-conductor).
- Validated by hw/test_rsim.py against in-game ground truth: xor_cell 4/4, fa_cell 8/8, and the pre-fix fa_cell reproduces the in-game failure exactly (4/8, sum ignores carry-in).
- Purpose: iterate MAC layouts offline; every design still gets an in-game test before it counts.

### 17.m Physical multiply-accumulate unit (2026-11-22)
- hw/mac.py system(): A <- A + x*w in one clock, x 4-bit unsigned, w 5-bit signed, A 13-bit signed (range -4096..4095, covers the 8-16-8 hidden-to-output sums -1920..2880).
- Array: 4 rows x 13 columns of one tileable cell (b = w AND x via one subtract comparator; full adder p = a^b, s = p^c, cout = max(c - (15 - p), a - p)); partial sums jog one column per row, so w lanes are straight and sign extension is a broadcast of w4.
- Register: 13 pulse latches (repeater locked by a LOCK row = 15 - pulse; pulse = GO - GO delayed 4 rt), per-bit reset comparator (d = A - RST) before each latch, feedback on a fourth layer (y=-56) over the array.
- 30,133 blocks, footprint 465 x 227. Commands only set x/w/GO/RST blocks and read latch states.
- Bug found in game, then modelled: dust power steps down only off a conductor (dust on glass sends power up, not down). rsim now models it; every descending step sits on stone.
- In game (docs/hw_mac_run1.txt): physical reset to 0, then 10 back-to-back ops incl. negative weights, 11/11 correct. Settle 8.6-13.1 s, write-back 7-12 s, MSPT 0.9-1.4 ms (20 TPS).

### 17.n MAC validation and throughput (2026-11-22)
- Ripple MAC in game: overflow wrap 22/22 (docs/hw_mac_overflow.txt); robustness 6/6: physical reset, input changes without GO leave A unchanged, 3 GO pulses = 3 MACs, reset asserted mid-computation, 30 s idle retention (docs/hw_mac_robust.txt).
- Wall-clock cycle sweep (inputs set, wait D, GO; A read once at the end): ripple correct at 17.3 s/op, wrong at 12.7 s/op. MSPT during switching P95 <= 24 ms, P99 <= 31 ms (20 TPS held).
- Critical path was the 13-bit carry ripple (about 7 repeaters per bit). Replaced by carry-save accumulation: state (S, C), carries go to the next row instead of along it, so an op has no horizontal ripple. Readout: 2 to 4 physical flush ops (x = 0) move carries out until C = 0, then S holds the binary value (no command-side addition).
- Clock skew: LOCK row now fed from its centre; bits 0..2 feedback lanes go straight up the east side.
- CSA in game (34,375 blocks, 393 x 275, docs/hw_csa_sweep.txt): correct at 13.0, 11.0 and 10.0 s/op, wrong at 8.0 s/op. Measured 10 s/op is 1.7x the ripple MAC. MSPT P99 <= 30 ms.
- Build bug found: forceload of more than 256 chunks fails silently; build() now slices forceload and spot-checks placed blocks.
- Inference estimates at the measured 10 s/op (MACs only, flush 4 ops per neuron, bias as one op; inhibition/activation unit not yet built):
  - 2-4-2, one MAC: 4x(2+1+4) + 2x(4+1+4) = 46 ops, about 7.7 min. With 4 MACs in parallel: 7 + 9 = 16 cycles, about 2.7 min.
  - 8-16-8, one MAC: 16x(1.5+1+4) + 8x(16+1+4) = 272 ops, about 45 min. With 8 MACs (one per output, hidden shared): about 13 + 21 = 34 cycles, about 6 min, ~280k blocks.

### 17.o One physical redstone neuron (2026-11-23)
- hw/neuron.py: y = clamp((w0*x0 + w1*x1 + b) // 4, 0, 15) on the carry-save MAC. Equation as reference.py output units (O_DIV = 4). Commands place data pins, pulse WE and START, and read block states. They never compute.
- Registers: 24 repeater latches (x0, x1 4 bit; w0, w1 5 bit signed; b 6 bit signed), written through 4 WE rows (LOCK_r = 15 - WE_r). Readback after the pins are cleared confirms physical storage.
- Crossbar: per stored bit, AND = data - NOTsel (one subtract comparator); OR into the MAC x/w lanes by glass climbs (one-way). Bias needs no command split: slot 3 is x = 2 with w = b bits 1..5, slot 4 is x = 1 with w = b bit 0.
- Sequencer: RUN latch (comparator loop) plus a 9-row delay-line raster, 40 repeaters per row = 160 rt per slot. Windows SEL_k = tap(k) - tap(k+1); GO_k = tap(a) - tap(a + 8 rt). Slots: 0 reset, 1-4 MAC ops, 5-7 carry flush (3 flushes always suffice: the lowest carry weight starts at 4 and rises 4 per op), row 8 strobes the output latch and clears RUN.
- Activation: S bits 2..12 tapped on L4 (floor /4 by wiring), sat = OR(q4..q9), out_k = (q_k | sat) - sign, 4-bit output latch + lamps.
- 49,164 blocks (MAC 34,375; sequencer 659 + crossbar 1,210 + activation 110 + lanes/taps ~12.8k), footprint 460 x 501.
- In game at (1000, 1300) vs simulator, same 10 cases (docs/hw_neuron_game.txt, docs/hw_neuron_sim.txt): 10/10 both. A, C and y identical in every case.
  - The cases cover saturation (481 -> 15), negative sums (-97, -4 -> 0), zero, the extreme -512, and floor of non-multiples (14 -> 3, 41 -> 10).
  - Weight change: w0 4 -> 8 with all else equal moved y from 4 to 9.
- Latency (in game, measured): load 4.8 s, START to RUN clear 143.3 s, output latch 0.6 s later, so about 149 s per evaluation. The next START must wait one slot (20 s used) while the delay line drains, so the cycle is about 170 s. Tick time P99 <= 43 ms (20 TPS held).
- Bugs found in game, then fixed and modelled:
  - The harness cleared data pins before the LOCK row re-asserted (1 s across 9 tiles).
  - 128 rt slots gave too little MAC settle in game (A = 112 for 225); 160 rt slots fixed it (settle >= 125 rt).
  - Redstone lamps are solid: a lit output latch powered the lamp, the lamp powered the adjacent lock row and froze the output latch. rsim now treats lamps as conductors, and the lock row moved one block off the lamps.
  - Restarting less than one slot after RUN clears corrupts the reset window.
- 2-4-2 feasibility at the measured 16 s slot:
  - Inhibition fits the MAC as one more op: (s - 4I)//4 = s//4 - I, so x = I, w = -4. The leak u + (d - u + 1)//2 = (d + u + 1)//2 is 3 MAC ops plus a 1-bit shift.
  - Per hidden neuron per step: about 9 slots plus about 7 for the leak. Per step, I = sum(u)//16 needs about 8 slots.
  - Total: about 4 x (4 x 16 + 8) + 2 x 10, roughly 310 slots, about 80 min on one MAC. With 4 MACs, one per hidden neuron (~200k blocks), about 20 min.
  - New hardware needed: u state registers fed from the activation output, a wider crossbar (inputs, u, I) and a longer sequencer.
  - Verdict: functionally achievable with the parts proven here. The slot time (MAC settle about 10 s in game) dominates, so shortening it comes before scaling.

### 17.p Tick-rate benchmark (2026-11-23)
- hw/test_neuron_tps.py: all harness waits are in game ticks, achieved TPS is measured from game time, and output is read after the strobe pulse is observed. 24/24 correct at 20, 30, 40, 60, 80 and 100 TPS (docs/hw_neuron_tps.md). Achieved TPS equalled the request at every rate.
- The computation is 2850 game ticks at any rate. At 100 TPS one evaluation takes 28.8 s (vs 144 s at 20 TPS) and the full cycle with drain about 34 s. The weight-change pair (w0 4 -> 8, y 4 -> 9) passed at every rate.

### 17.q Launch footage (2026-11-23)
- Capture client: Fabric 0.20.1 + ReplayMod 26.3-2.6.28 in isolated `clienttest/`, offline user Camera, spectator.
- Neuron take (`neuron_demo_vd20.mcpr`, 506 s, HW server view-distance raised 8 to 20 so the whole array is in the replay): w0=4 -> y=4, w0=8 -> y=9 at 20 TPS, 2850 game ticks each, strobe observed (docs/hw_demo_weight_change.txt, 17:04 to 17:09).
- Brain take (`brain_takes.mcpr`, 206 s): BrainUpright backed up to backups/ first; time frozen at midnight; 60 s idle, then two questions through sign + RUN (docs/video_brain_takes.txt).
- ReplayMod quirk: kicking or closing during recording leaves `.mcpr.tmp/changed/recording.tmcpr` unsaved. Rebuilt the .mcpr from the stream (parse [int32 time][int32 len][packet] records, duration = last time).
- Camera paths are code (video/shots.py). Each replay renders as one reel: per-shot centripetal Catmull-Rom splines joined by 1 ms linear hard cuts. video/edit.py trims by the cut table, adds captions (PIL, ffmpeg has no drawtext) and a synthesized drone.
- Time-lapse and speed-ups are labelled in the captions; the brain shots are captioned as the separate hybrid brain.
- Renders (2026-11-23 evening): one ReplayMod render per reel took about 1 to 1.5 min (not 30 as estimated). ReplayMod needs each interpolator to cover one contiguous run of segments ("Segments are not continuous" crash otherwise), so every cut has its own linear interpolator.
- Measured live: the brain's winning region starts lighting 21 s after RUN, is full by 22.5 s, stays lit until reset at about 43 s. The first activation shot (RUN + 7 to 15 s) missed it and was retimed.
- Output lamps change 2.9 s (w0=4) and 2.4 s (w0=8) into their shots; the "Output" captions start only after that, so no caption ever claims a value the lamps do not yet show.
- Final cut: release/redstone_cortex.mp4, 47.9 s, 2560 x 1440, 60 FPS.

### 17.r Question demo footage (2026-11-24)
- Feedback on the 47.9 s cut: captions too technical, and no demo of someone asking the brain a question. Recut with a user demo first and plain-English captions.
- Filmed on BrainUpright with ReplayMod (demo_takes.mcpr, video_demo_takes.txt): a survival player walks to the console, types "what is seven times eight" on the sign and presses RUN; second take "can you hear the music?". Input sent to the client as key events by video/film_demo.py.
- Failures on the way: `rotate ... facing` aims from the feet, so the player looked over the sign (fixed by computing yaw/pitch from eye height); the capture client binds "use" to R, so synthetic right-clicks did nothing (first take empty, marked in the log).
- Stage timing seen in the replay (1x): input lamps at RUN + 1.5 s, one of the 8 comparator rails held lit by RUN + 8 s, the winner's axon lane lights at about RUN + 17 s, the parietal region at RUN + 21 s.
- The question shots are all from one run, so the sign, comparators, axon and lit region show the same answer. The neuron section stays labelled as a separate build.
- Music: original track synthesized by video/music.py, replacing the drone.
- Final cut: release/redstone_cortex.mp4, 64.9 s, 2560 x 1440, 60 FPS, 251 MB.
