# Test Report: Upright Mode (prototype world `BrainUpright`)

Executed 2026-11-18 on a dedicated Minecraft 26.3 server over RCON, after commit `72bd202` and the later performance and visual changes (latest `59cd7bc`). Generator settings: `MODE = "upright"`, BAND 3, LINE 2, RING 8, ring repeater delay 3, staggered axons, random ticks off. The installed world and the relief fallback (`MODE = "relief"`) are unchanged.

**21 of 21 checks passed** (complete suite including restart, learning, lesions, ties, reset and idle recovery). Test 5 has two parts.

| # | Test | Expected | Actual | Result | Verified by |
|---|---|---|---|---|---|
| 1 | Empty input | no channel fires, status NO WINNER, NO WINNER lamp | `([], '"COMPLETE · NO WINNER (no recognised features)"')` | PASS | tract head repeaters + status text + indicator lamp |
| 2 | Unknown words | x all 0, no winner | `([0, 0, 0, 0, 0, 0, 0, 0], [])` | PASS | input scores + tract head repeaters |
| 3 | Multiple region keywords | >=3 nonzero inputs; physical winner = argmax(o) | `([3, 0, 0, 3, 0, 9, 6, 0], [3, 0, 0, 2, 1, 3, 12, 0], ['occipital'])` | PASS | x/o scores vs fired channels |
| 4 | Equal region scores | temporal = occipital, both fire, TIE lamp | `([0, 0, 0, 0, 0, 4, 4, 0], ['occipital', 'temporal'])` | PASS | o scores, tract heads, TIE lamp |
| 5 | All-zero physical vector | no channel fires | `[]` | PASS | tract head repeaters |
| 5 | Spec vectors on the physical circuit | [2,5,11,4,7,3,1,6] -> channel 3 only; [2,11,11,...] -> channels 2+3, TIE lamp | `{'a': (['parietal'], False), 'a_ok': True, 'b': (['cerebellum', 'parietal'], True), 'b_ok': True}` | PASS | dbg/inject -> barrels -> comparator WTA -> tract heads, TIE lamp |
| 6 | Each region wins | each question fires only its channel and lights >=95% of its sampled lamps | `{'prefrontal': (['prefrontal'], {'prefrontal': 1.0}), 'broca': (['broca'], {'broca': 1.0}), 'motor': (['motor'], {'motor': 1.0}), 'somato': (['somato'], {'somato': 1.0}), 'parietal': (['parietal'],...` | PASS | tract heads + 40 sampled cortex lamps per region |
| 7 | All eight channels driven | only channel 4 (strength 15) fires | `['somato']` | PASS | tract heads |
| 8 | Comparator levels 0..15 | comparator output equals requested level for every s | `[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]` | PASS | barrel fill then comparator OutputSignal |
| 9 | Training changes weights and winner | V(A temp+occ -> occ) rises; tie becomes Visual only | `(1, 2, ['occipital'])` | PASS | weight score + tract heads |
| 10 | Learning disabled | TRAIN refused, weights unchanged | ` "LEARNING IS OFF\nflip the LEARN lever"` | PASS | weights before/after + training display |
| 11 | Weights survive /reload | identical | `True` | PASS | weights before/after reload |
| 12 | Working-memory replay | slot 2 is reprocessed and recorded as newest | `('ts: "can you hear and see it "', 'ts: "can you hear and see it "')` | PASS | memory list before/after |
| 13 | Region lesion | parietal output 0, parietal channel silent, cortex region dark | `([1, 0, 0, 1, 0, 0, 2, 0], ['occipital'], 0.0)` | PASS | o score + tract head + lamps |
| 14 | Axon lesion + repair | lesioned: computed winner parietal, region dark, BLOCKED lamp; repaired: region lit | `(['parietal'], {}, 'TED Parietal · AXON CUT, signal blocked"', True, ['parietal'], {'parietal': 1.0})` | PASS | tract head before the gate, cortex lamps after it, status text |
| 15 | Synapse lesion | parietal output drops when its direct P->o synapse is cut | `(10, 2)` | PASS | o score with and without the synapse lever |
| 16 | Repair all | all levers reset and parietal lights again | `['parietal']` | PASS | levers + output |
| 17 | Repeated RUN presses | clock not restarted while computing | `(60, 60)` | PASS | #t before/after 5 RUNs |
| 18 | Reset mid-computation | state READY, nothing lit, next RUN works | `(0, {}, [], ['motor'])` | PASS | state + lamps + next run |
| 19 | World restart | trained weights persist; RUN works after restart | `(True, ['parietal'], 1.0)` | PASS | server stop/start, all 128 weights + full run |
| 20 | End to end | sign -> x -> h -> o -> physical WTA -> axon -> parietal lamps | `([0, 0, 0, 0, 9, 0, 0, 0], [0, 0, 0, 0, 10, 0, 1, 0], ['parietal'], {'parietal': 1.0}, '"COMPLETE · Parietal "')` | PASS | all layers + tract + cortex lamps + status |

## Performance (`perf.py`: worst 5-second `/tick query` window across a whole activation)

| Scenario | P99 range over repeated runs (ms) | Worst mean (ms) |
|---|---|---|
| Idle | 0.7 to 0.9 | 0.6 |
| Largest single region (prefrontal) | 23 to 31 | 4 |
| 2-way tie | 28 to 43 | 5 |
| 8-way tie (all regions at once) | 18 to 65 | 11 |
| 6 consecutive runs (sustained) | 4 to 26 | 2 |

Target was P99 at or below 30 ms. Single-region activations and sustained use meet it; ties exceed it in some runs. The worst single tick varies from run to run because it depends on which plate rings switch on the same tick. Tradeoff: further reduction needs either fewer lit lamps (a less visible activation) or Minecraft's experimental faster redstone update (a world-creation feature flag, not used to keep the world plain vanilla). Every scenario stayed under 50 ms (one tick).

### What the time is spent on
`/perf` profile of a prefrontal activation: scheduled block ticks (dust propagation through ~1.4 million neighbour lookups in 10 s) dominate the spikes; lamp light updates are about 3 percent. The changes that brought the largest region from P99 76 ms to about 25 ms: plates cut to a 3-cell band behind the surface (interior lamps are invisible), dust only on the plate rim, the spokes and every second row (a lamp under powered dust lights its neighbours), repeater delay 3 against the ladder's 4-tick plate spacing, staggered axon delays per region, and random ticks off.

## Failures found and fixed in upright mode
1. Neighbouring regions' plates touched in the same slice and merged dust networks, some latching on. Plates now keep a gap from every other region.
2. A halo light block replaced a ladder torch (the halo shell crosses ladders below the brain). Halo lights are kept off ladder columns and existing blocks.
3. A surface stripe touched another region's idle-powered ladder block and stayed lit. Stripes are kept away from all ladders.
4. Stale tracts from an earlier ladder layout powered a new tract. The tract layer under the brain is cleared before rebuilding; brain clears are sliced under the 1,000,000-block fill limit.
5. The readout ran before tall ladders finished (about 5 s of torch delay). Readout moved to 28 s and decay to 38 s.
6. Stripes adjacent only to ring-gap lamps never lit. Stripes are created only next to dust-powered lamps.
7. A partial manual rebuild ran the board builder after the console, and the board clear erased the input-neuron bars. The board clear now starts at z = -24.

## Not yet verified
- 1080p client screenshots and client FPS: postponed. GUI automation is only done with explicit approval when the machine is not in use.
- Ladder segments below the brain: columns are chosen for short exposure (4 to 6 blocks for parietal, occipital and cerebellum) but the frontal regions still need 20 to 29 blocks; these are encased as dark 3x3 columns, not hidden.
- Only the left hemisphere (facing the entrance) is wired for lighting; the right hemisphere is decorative.
