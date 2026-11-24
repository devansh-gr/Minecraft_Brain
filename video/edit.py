"""Final cut: trims the two ReplayMod reel renders (cut points from shots.reel), adds captions and an original
synthesized drone, exports 2560x1440 60 FPS H.264. Usage: python3 edit.py NEURON_REEL.mp4 BRAIN_REEL.mp4 OUT.mp4"""
import os, subprocess, sys, tempfile
from PIL import Image, ImageDraw, ImageFont
import shots

W, H, FPS = 2560, 1440, 60
FONT = "/System/Library/Fonts/HelveticaNeue.ttc"
# (reel, shot, start offset s, length s, caption, small label); CAP_AT: caption start (s into clip) where it must wait
# for the physical lamps (measured in the render: lamps change 2.9 s / 2.4 s into out4 / out8)
CAP_AT = {"out4": 2.0, "out8": 1.5}
EDL = [
    ("brain", "hook", 0.0, 5.0, "I built a brain in Minecraft.", ""),
    ("brain", "reveal", 0.0, 6.0, "", "Upright brain from an MRI atlas. 45,551 redstone lamps."),
    ("neuron", "flyover", 1.0, 8.0, "Then I built a neuron from pure redstone.", "Separate build. 49,164 blocks. 2x speed"),
    ("neuron", "reg4", 2.0, 3.0, "Store weight w0 = 4", "x0 = 5, x1 = 3, w1 = -2, bias = 3"),
    ("neuron", "lapse4", 1.0, 3.0, "The redstone multiplies and adds", "Time-lapse, about 28x. 2850 game ticks"),
    ("neuron", "out4", 1.0, 4.5, "Output: 4", "The 4 output lamps read 0100"),
    ("neuron", "reg8", 2.0, 3.0, "Change one weight: w0 = 8", "Same inputs and bias"),
    ("neuron", "out8", 1.0, 4.5, "Output: 9", "Lamps read 1001.  floor((8*5 - 2*3 + 3) / 4) = 9"),
    ("brain", "activate", 0.0, 6.0, "", "The hybrid brain: network in a datapack, winner-take-all in redstone comparators"),
    ("brain", "hero", 0.0, 5.0, "REDSTONE CORTEX", "A neural computing experiment in Minecraft"),
]


def caption(path, big, small):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    if big or small:                                      # soft bottom gradient for legibility
        for y in range(H - 420, H):
            d.line([(0, y), (W, y)], fill=(0, 0, 0, int(190 * (y - (H - 420)) / 420)))
    fb, fs = ImageFont.truetype(FONT, 96, index=1), ImageFont.truetype(FONT, 48, index=0)
    if big: d.text((W // 2, H - 200), big, font=fb, fill="white", anchor="ms", stroke_width=4, stroke_fill=(0, 0, 0))
    if small: d.text((W // 2, H - 110), small, font=fs, fill=(235, 235, 235), anchor="ms", stroke_width=3, stroke_fill=(0, 0, 0))
    im.save(path)


def main(neuron_mp4, brain_mp4, out):
    reels = {r: dict((n, (a / 1000, b / 1000)) for n, a, b in shots.reel(shots.REELS[r])[1]) for r in shots.REELS}
    src = {"neuron": neuron_mp4, "brain": brain_mp4}
    tmp = tempfile.mkdtemp(); parts = []
    for i, (r, n, off, ln, big, small) in enumerate(EDL):
        s0, s1 = reels[r][n]; t = s0 + off + 0.02                 # skip the cut frame
        ln = min(ln, round(s1 - t, 3)); EDL[i] = EDL[i][:3] + (ln,) + EDL[i][4:]   # never run into the next shot
        png = f"{tmp}/c{i}.png"; caption(png, big, small); p = f"{tmp}/p{i}.mp4"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.3f}", "-t", f"{ln}", "-i", src[r], "-loop", "1", "-t", f"{ln}", "-i", png,
                        "-filter_complex", f"[0:v]scale={W}:{H},fps={FPS},setsar=1[v];[1:v]format=rgba,fade=in:st={CAP_AT.get(n, 0.3)}:d=0.4:alpha=1,"
                        f"fade=out:st={ln - 0.5}:d=0.4:alpha=1[c];[v][c]overlay=0:0,format=yuv420p",
                        "-an", "-c:v", "libx264", "-preset", "slow", "-crf", "16", p], check=True)
        parts.append(p)
    total = sum(e[3] for e in EDL)
    open(f"{tmp}/list.txt", "w").write("".join(f"file '{p}'\n" for p in parts))
    # original drone: low fifths with slow swell, generated here
    drone = f"0.16*sin(2*PI*55*t)*(0.6+0.4*sin(2*PI*t/9))+0.10*sin(2*PI*82.5*t)+0.06*sin(2*PI*110*t)*(0.5+0.5*sin(2*PI*t/5))"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", f"{tmp}/list.txt",
                    "-f", "lavfi", "-t", f"{total}", "-i", f"aevalsrc={drone}:s=48000",
                    "-filter_complex", f"[0:v]fade=in:st=0:d=0.6,fade=out:st={total - 1.2}:d=1.2[v];"
                    f"[1:a]afade=in:st=0:d=2,afade=out:st={total - 2}:d=2[a]",
                    "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-r", str(FPS),
                    "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out], check=True)
    print(out, f"{total:.1f} s")


if __name__ == "__main__":
    main(*sys.argv[1:4])
