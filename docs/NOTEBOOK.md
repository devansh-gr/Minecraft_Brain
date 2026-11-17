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
