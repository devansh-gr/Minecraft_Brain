"""Final cut: trims the two ReplayMod reel renders (cut points from shots.reel), adds captions and an original
synthesized soundtrack (music.py), exports 2560x1440 60 FPS H.264. Usage: python3 edit.py BRAIN_REEL.mp4 LINK_REEL.mp4 OUT.mp4"""
import os, subprocess, sys, tempfile
from PIL import Image, ImageDraw, ImageFont
import shots

W, H, FPS = 2560, 1440, 60
FONT = "/System/Library/Fonts/HelveticaNeue.ttc"
# (reel, shot, start offset s, length s, caption, small label); CAP_AT: caption start (s into clip) where it must wait
# for the physical lamps (measured in the render: lamps change 2.9 s / 2.4 s into out4 / out8)
CAP_AT = {"l_out": 2.3}                                 # its output latches light 2.6 s into l_out (measured in the render)
TOP = {"l_write"}                                      # caption at the top so the sign text stays readable
EDL = [
    ("brain", "hook", 0.0, 4.5, "I built a brain in Minecraft", "Shaped from a real human brain scan"),
    ("link", "l_approach", 0.0, 4.0, "Walk up and ask it a question", ""),
    ("link", "l_write", 0.5, 4.5, "Write it on a sign", ""),
    ("link", "l_press", 0.0, 3.0, "Press RUN", ""),
    ("link", "l_proc", 0.0, 3.0, "The brain reads your question", ""),
    ("link", "l_flyover", 1.0, 5.5, "One of its neurons is pure redstone", "Its job: spot math. Sped up"),
    ("link", "l_lapse", 0.5, 4.0, "It works out how much math is in the question", "Sped up"),
    ("link", "l_out", 0.5, 5.0, "Lots of math, so its lamps light up", ""),
    ("link", "l_decide", 0.5, 5.0, "Every brain area competes for the question", "The math signal wins"),
    ("link", "l_axon", 0.0, 5.5, "The winner fires down a redstone nerve", ""),
    ("link", "l_lands", 0.0, 6.5, "and the brain's math area lights up", "Real brains do math here too"),
    ("brain", "hero", 0.0, 5.0, "REDSTONE CORTEX", "Built in vanilla Minecraft"),
]


def caption(path, big, small, top=False):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    if big or small:                                      # soft gradient (bottom, or top) for legibility
        for i in range(420):
            y = i if top else H - 1 - i
            d.line([(0, y), (W, y)], fill=(0, 0, 0, int(190 * (420 - i) / 420)))
    fb, fs = ImageFont.truetype(FONT, 96, index=1), ImageFont.truetype(FONT, 48, index=0)
    yb, ys = (200, 290) if top else (H - 200, H - 110)
    if big: d.text((W // 2, yb), big, font=fb, fill="white", anchor="ms", stroke_width=4, stroke_fill=(0, 0, 0))
    if small: d.text((W // 2, ys), small, font=fs, fill=(235, 235, 235), anchor="ms", stroke_width=3, stroke_fill=(0, 0, 0))
    im.save(path)


def main(brain_mp4, link_mp4, out):
    src = {"brain": brain_mp4, "link": link_mp4}
    reels = {r: dict((n, (a / 1000, b / 1000)) for n, a, b in shots.reel(shots.REELS[r])[1]) for r in src}
    tmp = tempfile.mkdtemp(); parts = []
    for i, (r, n, off, ln, big, small) in enumerate(EDL):
        s0, s1 = reels[r][n]; t = s0 + off + 0.02                 # skip the cut frame
        ln = min(ln, round(s1 - t, 3)); EDL[i] = EDL[i][:3] + (ln,) + EDL[i][4:]   # never run into the next shot
        png = f"{tmp}/c{i}.png"; caption(png, big, small, n in TOP); p = f"{tmp}/p{i}.mp4"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.3f}", "-t", f"{ln}", "-i", src[r], "-loop", "1", "-t", f"{ln}", "-i", png,
                        "-filter_complex", f"[0:v]scale={W}:{H},fps={FPS},setsar=1[v];[1:v]format=rgba,fade=in:st={CAP_AT.get(n, 0.3)}:d=0.4:alpha=1,"
                        f"fade=out:st={ln - 0.5}:d=0.4:alpha=1[c];[v][c]overlay=0:0,format=yuv420p",
                        "-an", "-c:v", "libx264", "-preset", "slow", "-crf", "16", p], check=True)
        parts.append(p)
    total = sum(e[3] for e in EDL)
    open(f"{tmp}/list.txt", "w").write("".join(f"file '{p}'\n" for p in parts))
    starts = [sum(e[3] for e in EDL[:i]) for i in range(len(EDL))]
    names = [e[1] for e in EDL]                                   # arpeggio enters with the demo, beat at the neuron
    here = os.path.dirname(os.path.abspath(__file__))
    subprocess.run([os.path.join(here, "../.venv/bin/python"), os.path.join(here, "music.py"), f"{total}", f"{tmp}/music.wav",
                    f"{starts[names.index('l_approach')]}", f"{starts[names.index('l_flyover')]}"], check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", f"{tmp}/list.txt",
                    "-i", f"{tmp}/music.wav",
                    "-filter_complex", f"[0:v]fade=in:st=0:d=0.6,fade=out:st={total - 1.2}:d=1.2[v];"
                    f"[1:a]afade=in:st=0:d=2,afade=out:st={total - 2}:d=2[a]",
                    "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-r", str(FPS),
                    "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out], check=True)
    print(out, f"{total:.1f} s")


if __name__ == "__main__":
    main(*sys.argv[1:4])
