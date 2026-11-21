import json, math
"""Shared constants and layout for the Redstone Cortex datapack generator."""

L0, L1 = -60, -59
DESK = -60
NAMES = {"prefrontal": "Prefrontal", "broca": "Broca", "motor": "Motor", "somato": "Touch",
         "parietal": "Parietal", "temporal": "Temporal", "occipital": "Visual", "cerebellum": "Cerebellum"}

# association units: pairs of regions that share a hidden neuron
PAIRS = [("prefrontal", "temporal"), ("broca", "temporal"), ("motor", "cerebellum"), ("motor", "somato"),
         ("somato", "parietal"), ("parietal", "occipital"), ("temporal", "occipital"), ("prefrontal", "parietal")]
W_P, W_A, V_P, V_A = 4, 2, 4, 1          # baseline weights
V_MIN, V_MAX = -8, 12                    # plasticity bounds
H_DIV, O_DIV = 4, 4                      # integer scaling of weighted sums
STEPS = 4                                # leaky integration steps

# console layout (y = -59 on a desk at y = -60)
CZ = -74                                 # main desk row
SIGN = (2, L1, CZ)
BTN = {"run": 4, "reset": 6, "train": 8, "reset_learning": 12, "demo": 14, "repair": 16, "memory": 20,
       "e1": 22, "e2": 24, "e3": 26, "e4": 28, "e5": 30}
LEV = {"learn": 10, "debug": 18}
REPLAY_X = [-14, -12, -10, -8, -6]
TZ = -78                                 # target-selection row
LZ = -70                                 # indicator lamp row
STAGES = ["stimulus", "input", "hidden", "output", "inhibition", "transmission", "decay"]
IND = {"ready": 18, "computing": 20, "complete": 22, "tie": 24, "nowinner": 26, "delivered": 28, "blocked": 30}

DEMO_QS = [["what is seven", "times eight?"], ["what colors are", "in a rainbow?"],
           ["how do i keep", "my balance on", "a skateboard"], ["how do you say", "hello in", "spanish"],
           ["should i quit", "my job?"]]
E3_Q = ["can you hear", "and see it?"]
E4_Q = ["what is seven", "times eight?"]
INJ = {"a": [2, 5, 11, 4, 7, 3, 1, 6], "b": [2, 11, 11, 4, 7, 3, 1, 6]}

# clock (game ticks after RUN)
T_IN, T_H, T_OUT, T_RAMP0, RAMP_DT, T_EXC, T_READ, T_DECAY, T_IDLE = 1, [12, 24, 36, 48], 60, 70, 6, 250, 640, 840, 860


