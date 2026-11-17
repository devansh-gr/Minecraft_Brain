# Test Report (v3)

Executed 2026-11-18 against a dedicated Minecraft 26.3 server over RCON with `test.py` (tests 1 to 18 and 20) and a scripted stop/start for test 19. Every result below was produced by running the test; none are inferred.

**21 of 21 checks passed.** Test 5 has two parts (all-zero vector and the two specification vectors).

| # | Test | Expected | Actual | Result | Verified by |
|---|---|---|---|---|---|
| 1 | Empty input | no channel fires, status NO WINNER, NO WINNER lamp | `([], '"COMPLETE · NO WINNER (no recognised features)"')` | PASS | tract head repeaters + status text + indicator lamp |
| 2 | Unknown words | x all 0, no winner | `([0, 0, 0, 0, 0, 0, 0, 0], [])` | PASS | input scores + tract head repeaters |
| 3 | Multiple region keywords | >=3 nonzero inputs; physical winner = argmax(o) | `([3, 0, 0, 3, 0, 9, 6, 0], [3, 0, 0, 2, 1, 3, 12, 0], ['occipital'])` | PASS | x/o scores vs fired channels |
| 4 | Equal region scores | temporal = occipital, both fire, TIE lamp | `([0, 0, 0, 0, 0, 4, 4, 0], ['temporal', 'occipital'])` | PASS | o scores, tract heads, TIE lamp |
| 5 | All-zero physical vector | no channel fires | `[]` | PASS | tract head repeaters |
| 5 | Spec vectors on the physical circuit | [2,5,11,4,7,3,1,6] -> channel 3 only; [2,11,11,...] -> channels 2+3, TIE lamp | `{'a': (['motor'], False), 'a_ok': True, 'b': (['broca', 'motor'], True), 'b_ok': True}` | PASS | dbg/inject -> barrels -> comparator WTA -> tract heads, TIE lamp |
| 6 | Each region wins | each question fires only its channel and lights >=95% of its sampled lamps | `{'prefrontal': (['prefrontal'], {'prefrontal': 0.97}), 'broca': (['broca'], {'broca': 1.0}), 'motor': (['motor'], {'motor': 1.0}), 'somato': (['somato'], {'somato': 1.0}), 'parietal': (['parietal'], {'parietal': 1.0})...` | PASS | tract heads + 40 sampled cortex lamps per region |
| 7 | All eight channels driven | only channel 4 (strength 15) fires | `['temporal']` | PASS | tract heads |
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
| 19 | World restart | trained weights, memory and state persist; RUN works after restart | `(2, ['parietal'])` | PASS | server stop/start, weights + memory + full run |
| 20 | End to end | sign -> x -> h -> o -> physical WTA -> axon -> parietal lamps | `([0, 0, 0, 0, 9, 0, 0, 0], [0, 0, 0, 0, 10, 0, 1, 0], ['parietal'], {'parietal': 1.0}, '"COMPLETE · Parietal "')` | PASS | all layers + tract + cortex lamps + status |

## Failure found and fixed during testing

Test 14 (axon lesion) initially failed: the lesioned axon still delivered the signal. A lever supplies strong (direct) power only to the block it is attached to, and a comparator's side input reads only direct power or dust. The lever was therefore moved to the floor and coupled to the comparator side through one dust block resting on glass (glass is not a conductor, so no other component is powered). After the change the test passed.

## Performance

`/tick query` sampled over the 100 ticks covering excitation, axon transmission and the cortex wave: mean 1.0 ms per tick, P50 0.9 ms, P95 1.5 ms, P99 3.9 ms (budget 50 ms).

## Not covered by automation

- Rendering, lighting quality and camera framing were not inspected in a game client; the test environment is a headless server.
- Most tests call the same functions the tick poller calls (`brain:ui/*`). The poller itself was checked separately: placing the RUN button in its pressed state started a computation within one second (state 1), and the run completed with the correct region (occipital for "what colors are in a rainbow"). A click by a real player was not performed.
