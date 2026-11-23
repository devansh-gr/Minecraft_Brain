# Physical neuron: tick-rate benchmark (isolated HW server, 2026-11-23)

Same 4 cases at each rate: y=15 (sum 481), w0=4 -> y=4, w0=8 -> y=9, y=0 (sum -97). Order high, mid, mid, low, so the output latch moves both ways.
Achieved TPS = game ticks / wall seconds over each run. Output read only after the strobe pulse is observed at the output-latch lock. Raw data: hw_neuron_tps.json. Harness: hw/test_neuron_tps.py.

| Requested TPS | Achieved TPS | Correct | START to output (s) | Load (s) | Tick P50 / P95 / P99 max (ms) | Budget (ms) |
|---|---|---|---|---|---|---|
| 20 | 20.0 | 4/4 | 144.0 | 5.4 | 15.3 / 25.5 / 30.9 | 50.0 |
| 30 | 30.0 | 4/4 | 96.0 | 3.6 | 14.3 / 21.1 / 140.7 | 33.3 |
| 40 | 40.0 | 4/4 | 72.0 | 2.8 | 11.5 / 17.4 / 22.9 | 25.0 |
| 60 | 60.0 | 4/4 | 48.0 | 1.9 | 10.5 / 16.2 / 18.2 | 16.7 |
| 80 | 80.0 | 4/4 | 36.0 | 1.4 | 10.4 / 15.9 / 17.4 | 12.5 |
| 100 | 100.0 | 4/4 | 28.8 | 1.2 | 6.2 / 15.4 / 19.2 | 10.0 |

- Every run took 2850 game ticks (START to RUN clear) at every rate: the circuit is clocked by game ticks, so wall time scales as 20/N.
- The next START waits 400 game ticks (one slot plus margin) for the delay line to drain: 20 s at 20 TPS, 4 s at 100 TPS.
- Full cycle at 100 TPS: about 1.2 s load + 28.8 s compute + 4 s drain = 34 s, vs about 170 s at 20 TPS.
- Tick-time percentiles come from /tick query (last 100 ticks), sampled during computation. At 60 TPS and above, single ticks exceed the nominal budget, but the measured game-time rate still met the target, so the server caught up. One 140.7 ms spike at 30 TPS, with no effect on results.
- Tick rate restored to 20 afterwards.
