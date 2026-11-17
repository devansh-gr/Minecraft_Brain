# Test Report (v3.2, visual round 2)

Executed 2026-11-18 against a dedicated Minecraft 26.3 server (test copy of the world) over RCON with `test.py`. Test 19 used a real server stop and start. Every row was produced by running the test after the latest change set (3D relief cortex, torch-ladder feeds, slope repeaters, 24-beacon banks, lamp-staircase neurons, lab lighting).

**21 of 21 checks passed.** Test 5 has two parts.

| # | Test | Expected | Actual | Result | Verified by |
|---|---|---|---|---|---|
| 1 | Empty input | no channel fires, status NO WINNER, NO WINNER lamp | `([], '"COMPLETE · NO WINNER (no recognised features)"')` | PASS | tract head repeaters + status text + indicator lamp |
| 2 | Unknown words | x all 0, no winner | `([0, 0, 0, 0, 0, 0, 0, 0], [])` | PASS | input scores + tract head repeaters |
| 3 | Multiple region keywords | >=3 nonzero inputs; physical winner = argmax(o) | `([3, 0, 0, 3, 0, 9, 6, 0], [3, 0, 0, 2, 1, 3, 12, 0], ['occipital'])` | PASS | x/o scores vs fired channels |
| 4 | Equal region scores | temporal = occipital, both fire, TIE lamp | `([0, 0, 0, 0, 0, 4, 4, 0], ['temporal', 'occipital'])` | PASS | o scores, tract heads, TIE lamp |
| 5 | All-zero physical vector | no channel fires | `[]` | PASS | tract head repeaters |
| 5 | Spec vectors on the physical circuit | [2,5,11,4,7,3,1,6] -> channel 3 only; [2,11,11,...] -> channels 2+3, TIE lamp | `{'a': (['motor'], False), 'a_ok': True, 'b': (['broca', 'motor'], True), 'b_ok': True}` | PASS | dbg/inject -> barrels -> comparator WTA -> tract heads, TIE lamp |
| 6 | Each region wins | each question fires only its channel and lights >=95% of its sampled lamps | `{'prefrontal': (['prefrontal'], {'prefrontal': 1.0}), 'broca': (['broca'], {'broca': 1.0}), 'motor': (['motor'], {'motor': 1.0}), 'somato': (['somato'], {'somato': 1.0}), 'parietal': (['parietal'], {'parietal': 1.0}),...` | PASS | tract heads + 40 sampled cortex lamps per region |
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
| 19 | World restart | trained weights persist; RUN works after restart | `(True, ['parietal'], 1.0)` | PASS | server stop/start, all 128 V compared + full run |
| 20 | End to end | sign -> x -> h -> o -> physical WTA -> axon -> parietal lamps | `([0, 0, 0, 0, 9, 0, 0, 0], [0, 0, 0, 0, 10, 0, 1, 0], ['parietal'], {'parietal': 1.0}, '"COMPLETE · Parietal "')` | PASS | all layers + tract + cortex lamps + status |

## Failures found and fixed

1. Axon lesion (test 14, v3): the lever drove only its attached block, so the gate comparator never saw it. It now feeds the comparator side through dust on glass.
2. Beacon shutters (v3.1): the sticky pistons stayed extended while their region was lit. Cause: quasi-connectivity. A piston also reads power at the space above it, and that space touched a lamp whose dust strongly powers it. Fix: the four lamp-layer neighbours of that space carry no dust (glass).
3. Test harness race (test 5, v3.1): the TIE lamp was sampled at a fixed 16 s, while the readout runs at about 16 s after an inject. The test now waits for state COMPLETE.

4. Ambient light blocks (visual 2d) were placed at y -48 over the whole lab and overwrote relief cortex blocks in 5 regions (test 6 failed). They are now kept outside the brain's footprint.
5. The readout checked delivery at the flat-map feed height (y -58); on the relief that block is a ladder torch, so axon cuts were reported as delivered (test 14 failed). The readout now uses each feed's real height.

## Additional verification
- `PHASE1_EVIDENCE.md` covers the forward pass, update semantics, bounds, and the 25-vector physical WTA sweep.
- `PHASE2_EVIDENCE.md` covers plasticity, A to B with exact weights, and the restart.
- `PHASE3_EVIDENCE.md` covers the lesion experiments.
- Beacon shutters: closed for all 8 regions at idle; only the firing regions open (parietal for parietal, temporal and occipital for the tie); all closed again after decay.
- In client (vanilla 26.3, test copy): a real RUN press, visible cortex lighting, a visible beacon beam, and the camera presets checked from screenshots in `img/`.

## Performance
`/tick query` over a full run after visual round 2 (24 beacons, relief cortex): mean 1.4 ms per tick, P50 1.4 ms, P95 2.1 ms, P99 3.9 ms (budget 50 ms). Before round 2: mean 1.0 ms.
