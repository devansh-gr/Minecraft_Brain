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


def fa_cell():
    """Comparator full adder: s = (a^b)^c, cout = p ? c : a with p = a^b.
    Inputs from the north: a floor (1,0,-3), b glass (4,2,-3), c glass (16,2,-3).
    Outputs: sum (5,0,16), cout (17,0,15)."""
    B = {}
    def put(dx, l, dz, b): B[(dx, l, dz)] = b
    X1, _, _ = xor_cell()
    B.update(X1)                                     # XOR1: p = a ^ b, p leaves at (2,0,6)
    X2, _, _ = xor_cell()
    B.update({(dx + 3, l, dz + 10): b for (dx, l, dz), b in X2.items()})  # XOR2: s = p ^ c
    # p: (2,7) -> repeater -> XOR2 a column at x=4, and east to the carry cell
    put(2, 0, 7, "redstone_wire"); put(3, 0, 7, REP % "west")
    for dx in (4, 5, 6, 7): put(dx, 0, 7, "redstone_wire")
    put(8, 0, 7, REP % "west"); put(9, 0, 7, "redstone_wire")
    put(10, 0, 7, "stone"); put(10, 1, 7, "redstone_wire")
    put(11, 1, 7, "stone"); put(11, 2, 7, "redstone_wire")
    for dx in range(12, 22):
        if dx == 17: put(17, 1, 7, "stone"); put(17, 2, 7, REP % "west")
        else: put(dx, 1, 7, "glass"); put(dx, 2, 7, "redstone_wire")
    for x in (13, 21):                               # two descents of p to the floor
        put(x, 1, 8, "stone"); put(x, 2, 8, "redstone_wire")
        put(x, 0, 9, "stone"); put(x, 1, 9, "redstone_wire")
    put(13, 0, 10, "redstone_wire"); put(13, 0, 11, "redstone_wire")
    for dz in (10, 11, 12): put(21, 0, dz, "redstone_wire")
    # c on glass: column x=16, branch west on z=-2 to the XOR2 b column at x=7
    for dz in range(-2, 3): put(16, 1, dz, "glass"); put(16, 2, dz, "redstone_wire")
    for dx in range(7, 16):
        if dx == 12: put(12, 1, -2, "stone"); put(12, 2, -2, REP % "east")
        else: put(dx, 1, -2, "glass"); put(dx, 2, -2, "redstone_wire")
    for dz in range(-1, 7):
        if dz == 3: put(7, 1, 3, "stone"); put(7, 2, 3, REP % "north")
        else: put(7, 1, dz, "glass"); put(7, 2, dz, "redstone_wire")
    put(16, 1, 3, "stone"); put(16, 2, 3, "redstone_wire")
    put(16, 0, 4, "stone"); put(16, 1, 4, "redstone_wire")
    for dz in range(5, 10): put(16, 0, dz, "redstone_wire")
    put(16, 0, 10, REP % "north"); put(16, 0, 11, REP % "north")
    # a: XOR1 row z=0 continues east to x=19, then south
    put(7, 0, 0, REP % "west")
    for dx in range(8, 20): put(dx, 0, 0, "redstone_wire")
    for dz in range(1, 11):
        put(19, 0, dz, REP % "north" if dz == 2 else "redstone_wire")
    # carry: NP = 15 - p, K = c - NP (c and p), G = a - p (a and not p), cout = K | G
    put(15, 0, 10, "redstone_block"); put(15, 0, 11, CMP % "north"); put(14, 0, 11, REP % "west")
    put(15, 0, 12, "redstone_wire"); put(16, 0, 12, CMP % "north")
    put(19, 0, 11, REP % "north"); put(19, 0, 12, CMP % "north"); put(20, 0, 12, REP % "east")
    for dx in range(16, 20): put(dx, 0, 13, "redstone_wire")
    for dz in (14, 15): put(17, 0, dz, "redstone_wire")
    return B, {"a": (1, 0, -3), "b": (4, 2, -3), "c": (16, 2, -3)}, {"s": (5, 0, 16), "cout": (17, 0, 15)}
