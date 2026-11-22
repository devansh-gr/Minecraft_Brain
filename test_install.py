"""Tests for install.py on throwaway saves in a temp dir. Run: python3 test_install.py"""
import os, shutil, tempfile, time
from pathlib import Path
import install as I

tmp = Path(tempfile.mkdtemp())
I.BACKUPS = tmp / "backups"  # does not exist yet: --backup must create it
fails = []


def world(name, parent):
    s = parent / name
    (s / "region").mkdir(parents=True)
    (s / "level.dat").write_bytes(os.urandom(64))
    (s / "region" / "r.0.0.mca").write_bytes(os.urandom(256))
    return s.resolve()


def refused(f, *a):
    try:
        f(*a)
    except SystemExit as e:
        return str(e)
    return None


def check(name, ok, info=""):
    print(("PASS " if ok else "FAIL ") + name, info)
    if not ok:
        fails.append(name)


A = world("W", tmp / "a")
B = world("W", tmp / "b")  # same name, different world
check("no backup refused", refused(I.verify, A) is not None)
I.backup(A)
check("backups/ created", I.BACKUPS.is_dir())
check("fresh backup verifies", refused(I.verify, A) is None)
check("wrong-world backup refused", "not" in (refused(I.verify, B) or ""), refused(I.verify, B))

time.sleep(1.1)
(A / "region" / "r.0.0.mca").write_bytes(os.urandom(256))
check("stale backup refused", "changed" in (refused(I.verify, A) or ""))

time.sleep(1.1)
bk = I.backup(A)
bk.write_bytes(bk.read_bytes()[:100])
check("corrupt archive refused", "checksum" in (refused(I.verify, A) or ""))
meta = bk.with_suffix(".json")
import json
m = json.loads(meta.read_text()); m["tgz_sha"] = I.sha(bk.read_bytes()); meta.write_text(json.dumps(m))
check("truncated archive refused", "unreadable" in (refused(I.verify, A) or ""), refused(I.verify, A))

dst = A / "datapacks" / "redstone_cortex"
dst.mkdir(parents=True)
(dst / "marker").write_text("working install")
real = shutil.copytree


def partial(src, d, **k):
    Path(d).mkdir()
    (Path(d) / "pack.mcmeta").write_text("{}")
    raise OSError("disk full")


shutil.copytree = partial
try:
    I.install(A)
except OSError:
    pass
check("failed copy keeps old install", (dst / "marker").exists() and not (A / ".rc_staging").exists())


def lossy(src, d, **k):
    shutil.copytree = real
    real(src, d, **k)
    shutil.copytree = lossy
    next(f for f in Path(d).rglob("*.mcfunction")).unlink()


shutil.copytree = lossy
try:
    I.install(A)
    check("bad staged copy rejected", False)
except RuntimeError:
    check("bad staged copy rejected", (dst / "marker").exists() and not (A / ".rc_staging").exists())

shutil.copytree = real
orig_rename = Path.rename


def swap_fail(self, target):
    if self.name == ".rc_staging":
        raise OSError("rename failed")
    return orig_rename(self, target)


Path.rename = swap_fail
try:
    I.install(A)
except OSError:
    pass
Path.rename = orig_rename
check("failed swap restores old install", (dst / "marker").exists() and not (A / ".rc_old").exists())

# killed mid-swap: original moved to .rc_old, no datapack in place, a half staging dir left behind
dst.rename(A / ".rc_old"); (A / ".rc_staging").mkdir()
shutil.copytree = partial
try:
    I.install(A)
except OSError:
    pass
shutil.copytree = real
check("interrupted swap recovered from .rc_old", (dst / "marker").exists() and not (A / ".rc_old").exists())

I.install(A)
check("install matches source, old removed", I.tree(dst) == I.tree(I.SRC) and not (A / ".rc_old").exists())

shutil.rmtree(tmp)
print(f"{len(fails)} failed" if fails else "ALL PASS")
