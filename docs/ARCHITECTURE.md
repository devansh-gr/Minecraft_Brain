# Architecture (v3)

Which computation happens where. Blue nodes run in the datapack (commands). Orange nodes are physical redstone. The handoff points are the barrels: the datapack writes item counts, and every decision after that is made by comparators.

```mermaid
flowchart LR
  subgraph A[Zone A: input terminal]
    S[Sign text] --> P[Parser: lowercase, tokens, suffix stripping, 863-word lexicon]
  end
  subgraph B[Zone B: neural processor]
    P --> X[8 input neurons x = min 15, 3 x hits]
    X --> H[16 hidden neurons, 4-step leaky integration, global inhibition]
    H --> O[8 output neurons o = clamp sum V h / 4]
    M[(Working memory, 5 records)] -. replay .-> X
    L[(Plastic weights V, persistent)] --> O
  end
  subgraph C[Zone C: inhibitory computer]
    O --> BR[Barrels: item count sets comparator level 0-15]
    BR --> MX[Comparator max chain + broadcast]
    MX --> D[Decision comparators: fire if o_k >= max]
    BR --> D
  end
  subgraph D2[Zone D: axons]
    D --> AX[Repeater all-or-none, lamp axon, subtract-mode lesion gate]
  end
  subgraph E[Zone E: cortex]
    AX --> CX[Dust meshes on 12,856 lamps, repeater rings]
  end
  D --> RD[Readout: datapack reads which tract heads are powered]
  CX --> RD
  RD --> M
  classDef dp fill:#1f3b63,color:#fff
  classDef rs fill:#7a3a12,color:#fff
  class P,X,H,O,M,L,RD dp
  class BR,MX,D,AX,CX rs
```

| Function | Implementation | Why |
|---|---|---|
| Reading the sign, tokenising, lexicon lookup | Datapack | Redstone cannot read text |
| 8-16-8 network arithmetic (about 300 multiply-adds per run) | Datapack scoreboards | Integer multiplication at this scale is impractical in blocks |
| Working memory, plastic weights, training rule | Datapack storage and scoreboards | Persistent state with 128 plastic synapses |
| Score to signal strength | Barrel item counts read by comparators | Physical analog encoding, verified for all 16 levels |
| Finding the maximum, suppressing weaker channels, ties | Comparator chain and decision comparators | Physical winner-take-all; the datapack never chooses the winner |
| Visible competition | Display comparators driving lamp bars while inhibition ramps | Physical comparison; the ramp only changes when inhibitory barrels fill |
| Axon transmission and axon lesions | Repeaters, dust on lamps, subtract-mode comparator gated by a lever | Physical interruption |
| Cortex activation | Dust meshes and 1,698 repeaters | Physical; no command touches a cortex lamp |
| Region lesion, synapse lesion | Datapack reads the lever and zeroes the neuron or synapse | Applied to the numerical model, which then feeds the physical circuit |
| Reporting the outcome (status text, memory) | Datapack reads tract and cortex block states | Read-only observation of the physical result |

Command blocks in the world: zero. Console buttons are polled by the datapack tick function (rising-edge detection).
