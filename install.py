"""Install the generated datapack into a world save. Refuses unless a backup of that save exists that is newer
than every file in it, and unless --yes is given after the warning. Does not run the build: in game,
/function brain:build warns again and only proceeds once #build_ok is set.

  python3 install.py <save_dir> --backup     make a backup in backups/ (do this with the game closed)
  python3 install.py <save_dir> --yes        install the datapack from build/datapack
"""
import shutil, sys, tarfile, time
from pathlib import Path

ROOT = Path(__file__).parent
SRC = ROOT / "build" / "datapack" / "redstone_cortex"
BOX = (ROOT / "build" / "datapack" / "redstone_cortex" / "data/brain/function/build.mcfunction")


def newest(save):
    return max(f.stat().st_mtime for f in save.rglob("*") if f.is_file())


def backups(save):
    return sorted((ROOT / "backups").glob(f"install-{save.name}-*.tgz"), key=lambda f: f.stat().st_mtime)


if __name__ == "__main__":
    if len(sys.argv) < 2 or not (Path(sys.argv[1]) / "level.dat").exists():
        sys.exit(__doc__)
    save = Path(sys.argv[1]).resolve()
    if "--backup" in sys.argv:
        out = ROOT / "backups" / f"install-{save.name}-{time.strftime('%Y%m%d-%H%M%S')}.tgz"
        with tarfile.open(out, "w:gz") as t:
            t.add(save, arcname=save.name)
        sys.exit(f"backup written: {out}")
    b = backups(save)
    if not b or b[-1].stat().st_mtime < newest(save):
        sys.exit(f"REFUSED: no backup of {save.name} newer than its last change. Run with --backup first (game closed).")
    print(f"Backup found: {b[-1].name}")
    print("WARNING: after install, /function brain:build clears and rebuilds "
          + BOX.read_text().split("will CLEAR ")[1].split(" and rebuild")[0] + " in this world.")
    if "--yes" not in sys.argv:
        sys.exit("Not installed. Re-run with --yes to install the datapack.")
    dst = save / "datapacks" / "redstone_cortex"
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(SRC, dst)
    print(f"Installed datapack into {dst}. Nothing was built; the world blocks are unchanged.")
