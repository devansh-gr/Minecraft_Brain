import socket, struct, sys
def cmd(c, s=[None]):
    if s[0] is None:
        s[0] = socket.create_connection(("127.0.0.1", 25599)); _send(s[0], 3, "brain"); _recv(s[0])
    _send(s[0], 2, c); return _recv(s[0])
def _send(s, t, p):
    d = struct.pack("<ii", 1, t) + p.encode() + b"\0\0"; s.sendall(struct.pack("<i", len(d)) + d)
def _recv(s):
    n = struct.unpack("<i", s.recv(4))[0]; b = b""
    while len(b) < n: b += s.recv(n - len(b))
    return b[8:-2].decode(errors="replace")
if __name__ == "__main__":
    for c in sys.argv[1:]: print(">", c, "\n", cmd(c)[:600])
