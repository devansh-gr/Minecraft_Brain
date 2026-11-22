"""Hand-placed compact cells (comparator logic), relative coordinates (dx, layer, dz); layer 0 = floor y=-60."""
Y = {0: -60, 1: -59, 2: -58}
CMP = "comparator[facing=%s,mode=subtract]"
REP = "repeater[facing=%s]"
# facing = side the input comes from: flow +z -> north, -z -> south, +x -> west, -x -> east


def xor_cell():
    """a enters from the north on the floor at dx=1, b from the north on glass (layer 2) at dx=4.
    Output dust leaves south at dx=2. Returns blocks, input feed points, output point."""
    B = {}
    def put(dx, l, dz, b): B[(dx, l, dz)] = b
    # comparators: C1 = a - b at (1,3), C2 = b - a at (4,3), both flowing south
    put(1, 0, 3, CMP % "north"); put(4, 0, 3, CMP % "north")
    put(1, 0, 2, REP % "north")                      # C1 rear <- a
    put(0, 0, 3, REP % "west"); put(-1, 0, 3, "redstone_wire")   # C1 side <- b (from the west)
    put(4, 0, 2, REP % "north")                      # C2 rear <- b
    put(5, 0, 3, REP % "east"); put(6, 0, 3, "redstone_wire")    # C2 side <- a (from the east)
    # a on the floor: column x=1, branch east along z=0 to x=6, then south to the C2 side feed
    for dz in (-2, -1, 0, 1): put(1, 0, dz, "redstone_wire")
    for dx in range(2, 7): put(dx, 0, 0, "redstone_wire")
    for dz in (1, 2): put(6, 0, dz, "redstone_wire")
    # b on glass: column x=4 from the north, over a's row at z=0, steps down to the C2 rear feed at z=1
    for dz in (-2, -1): put(4, 1, dz, "glass"); put(4, 2, dz, "redstone_wire")
    put(4, 1, 0, "stone"); put(4, 2, 0, "redstone_wire")
    put(4, 0, 1, "stone"); put(4, 1, 1, "redstone_wire")
    # b branch west on glass along z=-2 to x=-1, steps down there and runs south to the C1 side feed
    for dx in range(-1, 4): put(dx, 1, -2, "glass"); put(dx, 2, -2, "redstone_wire")
    put(-1, 1, -2, "stone")
    put(-1, 0, -1, "stone"); put(-1, 1, -1, "redstone_wire")
    for dz in (0, 1, 2): put(-1, 0, dz, "redstone_wire")
    # output: C1 and C2 merge on z=4, leave south at x=2
    for dx in range(1, 5): put(dx, 0, 4, "redstone_wire")
    for dz in (5, 6): put(2, 0, dz, "redstone_wire")
    return B, {"a": (1, 0, -3), "b": (4, 2, -3)}, (2, 0, 6)


def at(B, x0, z0):
    return {(x0 + dx, Y[l], z0 + dz): b for (dx, l, dz), b in B.items()}
