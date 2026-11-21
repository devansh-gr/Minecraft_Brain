# Test Report: Upright Mode (prototype world `BrainUpright`)

Executed 2026-11-18, rerun in full 2026-11-21 after commit `27eb9ce` (hidden feeds, light seal, axon stagger), on a dedicated Minecraft 26.3 server over RCON, after commit `72bd202` and the later performance and visual changes (latest `59cd7bc`). Generator settings: `MODE = "upright"`, BAND 3, LINE 2, RING 8, ring repeater delay 3, axon stagger 5 redstone ticks per board column, tinted-glass interior seal, hidden feeds (RISER_EXPOSED 8, MAX_LOSS 0.15), random ticks off. The installed world and the relief fallback (`MODE = "relief"`) are unchanged.

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

| Scenario | P99, 2026-11-18 (ms) | P99, 2026-11-21, 2 runs (ms) | Worst mean, 2026-11-21 (ms) |
|---|---|---|---|
| Idle | 0.7 to 0.9 | 0.7 | 0.6 |
| Largest single region (prefrontal) | 23 to 31 | 12.5, 20.9 | 0.8 |
| 2-way tie | 28 to 43 | 27.1, 27.1 | 5.5 |
| 8-way tie (all regions at once) | 18 to 65 | 23.7, 27.5 | 2.9 |
| 6 consecutive runs (sustained) | 4 to 26 | 21.2 to 27.7 | 2.4 |

Target P99 at or below 30 ms: met in all 11 measured windows. Three changes, measured separately:
1. Tinted-glass light seal: every unused cell inside the brain is tinted glass (blocks light, conducts no redstone), so a switching lamp relights only its own few cells instead of the hollow interior. Commit `615a636`: 2-way tie 22 ms, 8-way tie 43 ms.
2. Axon stagger: each board column adds 5 redstone ticks (0.25 s) of repeater delay, so tied regions climb their ladders in turn instead of together. The stagger used before (0 to 4 ticks) could not separate ladders, because plates repeat every 2 redstone ticks and redstone ticks are the finest timing step. A tie now lights as a west-to-east cascade over 1.75 s. Readout moved from 28 s to 32 s, decay from 38 s to 42 s.
3. Dropped items: each rebuild popped torches and dust as item entities (8,847 found, about 30 ms per tick while idle). The build now kills dropped items. Earlier benchmark runs were partly affected by this.

Rejected: dust on every third row instead of every second (dust down 15 percent but lit lamps down 25 percent), and plates cut down to cells that touch the shell (lamps behind the surface down 44 percent, because the thinned plates broke away from their ladders).

### What the time is spent on
`/perf` profile of a prefrontal activation: scheduled block ticks (dust propagation through ~1.4 million neighbour lookups in 10 s) dominate the spikes; lamp light updates are about 3 percent. The changes that brought the largest region from P99 76 ms to about 25 ms: plates cut to a 3-cell band behind the surface (interior lamps are invisible), dust only on the plate rim, the spokes and every second row (a lamp under powered dust lights its neighbours), repeater delay 3 against the ladder's 4-tick plate spacing, staggered axon delays per region, and random ticks off.

## Hidden feeds (stilts)
Regions whose ladder would stand more than 6 blocks below the brain (prefrontal 29, Broca 29, somatosensory 20, motor 19) are fed by a short riser column under the posterior brain instead. At one plate level the riser's powered block drives a dust line on glass that runs inside the brain to the region's ladder, which continues upward from there. Route search: Dijkstra over interior cells at least one cell from the dark backing layer. It costs 1000 per cell inside another region's plate band, 3 per turn, and requires straight ends so the first and last cells can hold repeaters. Repeaters come at least every 10 dust. The riser site is chosen by the same costs plus lane spacing (3 blocks) for the tract under the board. Plates below the crossing level are not built: they cost prefrontal 17 percent and Broca 22 percent of their lit lamps (the orbitofrontal underside). In-game check: the four rerouted regions light fully when injected alone (lit fraction 1.0), and the regression passes.

## Failures found and fixed in upright mode
1. Neighbouring regions' plates touched in the same slice and merged dust networks, some latching on. Plates now keep a gap from every other region.
2. A halo light block replaced a ladder torch (the halo shell crosses ladders below the brain). Halo lights are kept off ladder columns and existing blocks.
3. A surface stripe touched another region's idle-powered ladder block and stayed lit. Stripes are kept away from all ladders.
4. Stale tracts from an earlier ladder layout powered a new tract. The tract layer under the brain is cleared before rebuilding; brain clears are sliced under the 1,000,000-block fill limit.
5. The readout ran before tall ladders finished (about 5 s of torch delay). Readout moved to 28 s and decay to 38 s.
6. Stripes adjacent only to ring-gap lamps never lit. Stripes are created only next to dust-powered lamps.
7. A partial manual rebuild ran the board builder after the console, and the board clear erased the input-neuron bars. The board clear now starts at z = -24.

8. First hidden-feed version: one line went 16 dust without a repeater around a bend and died; one line's first repeater sat on a turn and powered nothing. The search now penalises turns and requires straight ends, and repeaters are forced every 10 dust (with an assertion).
9. Dropped item entities from rebuilds raised idle tick time to about 30 ms. The build now kills them.

## Not yet verified
- 1080p client screenshots and client FPS: postponed. GUI automation is only done with explicit approval when the machine is not in use.
- Ladder segments below the brain: now 4 to 8 blocks for seven regions (encased 3x3 columns under the posterior brain). Temporal still stands 14 blocks: hiding it would remove 21 percent of its plate area. See "Hidden feeds".
- Only the left hemisphere (facing the entrance) is wired for lighting; the right hemisphere is decorative.
