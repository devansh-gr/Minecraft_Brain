"""Install the generated datapack into a world save. Refuses unless a verified backup of that exact save exists
and the save has not changed since, and unless --yes is given after the warning. Does not run the build: in game,
/function brain:build warns again and only proceeds once #build_ok is set.

  python3 install.py <save_dir> --backup     make a backup in backups/ (do this with the game closed)
  python3 install.py <save_dir> --yes        install the datapack from build/datapack
"""
import hashlib, json, shutil, sys, tarfile, time
from pathlib import Path

ROOT = Path(__file__).parent
BACKUPS = ROOT / "backups"
SRC = ROOT / "build" / "datapack" / "redstone_cortex"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def newest(save):
    return max(f.stat().st_mtime for f in save.rglob("*") if f.is_file())


def tree(d):
    return {str(f.relative_to(d)): sha(f.read_bytes()) for f in d.rglob("*") if f.is_file()}


def backup(save):
    BACKUPS.mkdir(parents=True, exist_ok=True)
    out = BACKUPS / f"install-{save.name}-{time.strftime('%Y%m%d-%H%M%S')}.tgz"
    with tarfile.open(out, "w:gz") as t:
        t.add(save, arcname=save.name)
    meta = {"save": str(save), "newest": newest(save), "level_sha": sha((save / "level.dat").read_bytes()),
            "tgz_sha": sha(out.read_bytes())}
    out.with_suffix(".json").write_text(json.dumps(meta))
    return out


def verify(save):
    """Returns the backup path, or raises SystemExit with the reason."""
    b = sorted(BACKUPS.glob(f"install-{save.name}-*.tgz")) if BACKUPS.exists() else []
    if not b or not b[-1].with_suffix(".json").exists():
        sys.exit(f"REFUSED: no backup of {save.name}. Run with --backup first (game closed).")
    b = b[-1]
    meta = json.loads(b.with_suffix(".json").read_text())
    if meta["save"] != str(save):
        sys.exit(f"REFUSED: newest backup {b.name} is of {meta['save']}, not {save}.")
    if sha(b.read_bytes()) != meta["tgz_sha"]:
        sys.exit(f"REFUSED: {b.name} does not match its recorded checksum.")
    try:
        with tarfile.open(b, "r:gz") as t:
            names = set()
            for m in t:
                names.add(m.name)
                if m.isfile():
                    data = t.extractfile(m).read()
                    if m.name == f"{save.name}/level.dat":
                        level = data
    except (tarfile.TarError, OSError, EOFError) as e:
        sys.exit(f"REFUSED: {b.name} is unreadable ({e}).")
    if f"{save.name}/level.dat" not in names or sha(level) != meta["level_sha"]:
        sys.exit(f"REFUSED: {b.name} does not contain this world's level.dat.")
    if sha((save / "level.dat").read_bytes()) != meta["level_sha"] or newest(save) > meta["newest"]:
        sys.exit(f"REFUSED: {save.name} changed after backup {b.name}. Run with --backup again (game closed).")
    return b


def install(save):
    """Copy to a staging dir, check it against the source, then swap. The old install is kept until the swap
    succeeds and restored if it fails."""
    dst, stage, old = save / "datapacks" / "redstone_cortex", save / ".rc_staging", save / ".rc_old"
    # recover an interrupted earlier run: old moved away but the new copy never renamed in, so old is the
    # only working copy. If dst exists the atomic rename completed and old is a leftover.
    if old.exists() and not dst.exists():
        old.rename(dst)
    for d in (stage, old):
        if d.exists():
            shutil.rmtree(d)
    want = tree(SRC)
    try:
        shutil.copytree(SRC, stage)
        if tree(stage) != want or not (stage / "pack.mcmeta").exists():
            raise RuntimeError("staged copy does not match build/datapack")
        dst.parent.mkdir(exist_ok=True)
        if dst.exists():
            dst.rename(old)
        try:
            stage.rename(dst)
        except BaseException:
            if old.exists() and not dst.exists():
                old.rename(dst)
            raise
    finally:
        if stage.exists():
            shutil.rmtree(stage)
    if old.exists():
        shutil.rmtree(old)
    return dst


if __name__ == "__main__":
    if len(sys.argv) < 2 or not (Path(sys.argv[1]) / "level.dat").exists():
        sys.exit(__doc__)
    save = Path(sys.argv[1]).resolve()
    if "--backup" in sys.argv:
        sys.exit(f"backup written: {backup(save)}")
    print(f"Backup verified: {verify(save).name}")
    box = (SRC / "data/brain/function/build.mcfunction").read_text().split("will CLEAR ")[1].split(" and rebuild")[0]
    print(f"WARNING: after install, /function brain:build clears and rebuilds {box} in this world.")
    if "--yes" not in sys.argv:
        sys.exit("Not installed. Re-run with --yes to install the datapack.")
    print(f"Installed datapack into {install(save)}. Nothing was built; the world blocks are unchanged.")
