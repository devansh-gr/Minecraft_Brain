"""Original soundtrack, synthesized here (no samples). Am-F-C-G at 96 BPM: pad, then arpeggio, then pulse and kick.
Usage: python3 music.py SECONDS OUT.wav [ARP_AT KICK_AT]"""
import sys, wave
import numpy as np

SR, BPM = 48000, 96
BEAT = 60 / BPM
CHORDS = [(57, 60, 64), (53, 57, 60), (48, 52, 55), (55, 59, 62)]   # Am F C G (MIDI)
hz = lambda m: 440 * 2 ** ((m - 69) / 12)


def lowpass(x, a):
    y = np.empty_like(x); s = 0.0
    for i, v in enumerate(x): s += a * (v - s); y[i] = s
    return y


def track(dur, arp_at, kick_at):
    n = int(dur * SR); t = np.arange(n) / SR; out = np.zeros(n)
    bar = 4 * BEAT
    for k in range(int(dur / bar) + 1):                       # pad: detuned saws, one chord per bar
        a, b = int(k * bar * SR), min(n, int((k + 1) * bar * SR))
        if a >= n: break
        tt = t[a:b] - k * bar; env = np.minimum(1, tt / 0.6) * np.minimum(1, (bar - tt) / 0.4)
        for m in CHORDS[k % 4] + (CHORDS[k % 4][0] - 12,):
            for d in (-0.08, 0.08):
                ph = (hz(m + d) * tt) % 1; out[a:b] += 0.035 * (2 * ph - 1) * env
    out = lowpass(out, 0.06)
    step = BEAT / 2                                            # arpeggio: eighth-note plucks
    for i in range(int((dur - arp_at) / step)):
        s = arp_at + i * step; a = int(s * SR); b = min(n, a + int(0.5 * SR))
        ch = CHORDS[int(s / bar) % 4]; m = (ch + (ch[0] + 12,))[[0, 1, 2, 3, 2, 1, 0, 2][i % 8]] + 12
        tt = np.arange(b - a) / SR; v = np.sin(2 * np.pi * hz(m) * tt) * np.exp(-tt * 7) * 0.12
        out[a:b] += v
        if b + int(0.375 * SR) < n: out[a + int(0.375 * SR):b + int(0.375 * SR)] += 0.35 * v   # dotted-eighth echo
    for i in range(int((dur - kick_at) / BEAT)):               # soft kick + sub pulse on each beat
        a = int((kick_at + i * BEAT) * SR); b = min(n, a + int(0.3 * SR)); tt = np.arange(b - a) / SR
        out[a:b] += 0.30 * np.sin(2 * np.pi * (45 + 90 * np.exp(-tt * 30)) * tt) * np.exp(-tt * 9)
    swell = np.clip((t - (dur - 8)) / 5, 0, 1)                  # lift into the ending
    out *= 1 + 0.5 * swell
    out *= np.minimum(1, t / 2) * np.minimum(1, (dur - t) / 2.5)
    return np.tanh(out * 1.6) * 0.8


if __name__ == "__main__":
    dur = float(sys.argv[1]); x = track(dur, *(map(float, sys.argv[3:5]) if len(sys.argv) > 4 else (dur * 0.12, dur * 0.45)))
    pcm = (np.repeat(x[:, None], 2, 1) * 32767).astype(np.int16)
    with wave.open(sys.argv[2], "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
    print(sys.argv[2], f"{dur} s")
