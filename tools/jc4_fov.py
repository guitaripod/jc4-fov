#!/usr/bin/env python3
"""Rebuild the dropzone payload from an installed copy of Just Cause 4.

Reads the camera entity files out of the game's .tab/.arc archives, rewrites every
`FOV` property in them, and writes the result to dropzone/ as loose files.
"""
import argparse
import glob
import os
import struct
import subprocess
import sys
import tempfile

TARGETS = [
    "editor/entities/characters/main_characters/rico.epe",
    "editor/entities/weapons/03_mounted/wpn_201_minigun/w201_minigun_mount.epe",
    "editor/entities/weapons/03_mounted/wpn_201_minigun/w201_minigun_mount_rebel.epe",
    "editor/entities/weapons/04_stationary/wpn_202_cannon/wpn_202_cannon.epe",
    "editor/entities/weapons/04_stationary/wpn_202_cannon/wpn_202_cannon_rebel.epe",
    "editor/entities/weapons/04_stationary/wpn_203_aa_gun/wpn_203_aa_gun.epe",
    "editor/entities/weapons/04_stationary/wpn_203_aa_gun/wpn_203_aa_gun_rebel.epe",
    "editor/entities/weapons/04_stationary/wpn_204_mortar/wpn_204_mortar_mounted.epe",
    "editor/entities/weapons/04_stationary/wpn_204_mortar/wpn_204_mortar_mounted_rebel.epe",
]

MOUNT_ORDER = [
    "boot_patch", "boot_patch/eng", "boot", "boot/hires",
    "main_patch", "main_patch/hires", "main_patch/eng",
    "main", "main/hires", "main/eng",
    "cp_deathstalker", "cp_deathstalker/hires", "cp_digitaldeluxe", "cp_digitaldeluxe/hires",
    "cp_neonracer", "cp_neonracer/hires", "cp_renegade", "cp_renegade/hires",
]

MASK = 0xFFFFFFFF


def _rot(x, k):
    return ((x << k) | (x >> (32 - k))) & MASK


def hash_jenkins(text):
    """Jenkins lookup3 as Avalanche's Apex engine hashes VFS names and properties."""
    data = text.encode("ascii")
    length = len(data)
    a = b = c = (0xDEADBEEF + length) & MASK
    i = 0
    while i + 12 < length:
        a = (a + int.from_bytes(data[i:i + 4], "little")) & MASK; i += 4
        b = (b + int.from_bytes(data[i:i + 4], "little")) & MASK; i += 4
        c = (c + int.from_bytes(data[i:i + 4], "little")) & MASK; i += 4
        a = (a - c) & MASK; a ^= _rot(c, 4); c = (c + b) & MASK
        b = (b - a) & MASK; b ^= _rot(a, 6); a = (a + c) & MASK
        c = (c - b) & MASK; c ^= _rot(b, 8); b = (b + a) & MASK
        a = (a - c) & MASK; a ^= _rot(c, 16); c = (c + b) & MASK
        b = (b - a) & MASK; b ^= _rot(a, 19); a = (a + c) & MASK
        c = (c - b) & MASK; c ^= _rot(b, 4); b = (b + a) & MASK
    for shift, reg in ((0, 'a'), (8, 'a'), (16, 'a'), (24, 'a'),
                       (0, 'b'), (8, 'b'), (16, 'b'), (24, 'b'),
                       (0, 'c'), (8, 'c'), (16, 'c'), (24, 'c')):
        if i >= length:
            break
        v = data[i] << shift
        if reg == 'a':
            a = (a + v) & MASK
        elif reg == 'b':
            b = (b + v) & MASK
        else:
            c = (c + v) & MASK
        if not (reg == 'c' and shift == 24):
            i += 1
    c ^= b; c = (c - _rot(b, 14)) & MASK
    a ^= c; a = (a - _rot(c, 11)) & MASK
    b ^= a; b = (b - _rot(a, 25)) & MASK
    c ^= b; c = (c - _rot(b, 16)) & MASK
    a ^= c; a = (a - _rot(c, 4)) & MASK
    b ^= a; b = (b - _rot(a, 14)) & MASK
    c ^= b; c = (c - _rot(b, 24)) & MASK
    return c


def read_table(path):
    """Parse a TAB v2.1 archive index into its entry list."""
    data = open(path, "rb").read()
    magic, major, minor = struct.unpack_from("<IHH", data, 0)
    if magic != 0x00424154 or (major, minor) != (2, 1):
        raise ValueError(f"{path}: not a TAB 2.1 file")
    block_count, = struct.unpack_from("<I", data, 24)
    offset = 28 + 8 * block_count
    entries = {}
    while offset + 20 <= len(data):
        name_hash, entry_offset, csize, usize, block_index, ctype, flags = \
            struct.unpack_from("<IIIIHBB", data, offset)
        entries[name_hash] = dict(offset=entry_offset, csize=csize, usize=usize,
                                  block=block_index, ctype=ctype, flags=flags)
        offset += 20
    return entries


def locate(game_dir):
    """Map each target path to the archive entry the game's VFS would win with."""
    archives = os.path.join(game_dir, "archives_win64")
    found = {}
    for rank, mount in enumerate(MOUNT_ORDER):
        for tab in sorted(glob.glob(os.path.join(archives, mount, "*.tab"))):
            if os.path.relpath(os.path.dirname(tab), archives).replace(os.sep, "/") != mount:
                continue
            entries = read_table(tab)
            for name in TARGETS:
                if name in found:
                    continue
                entry = entries.get(hash_jenkins(name))
                if entry:
                    found[name] = (tab[:-4] + ".arc", entry)
    return found


def oodle_decompress(jobs, game_dir, helper):
    """Run the mingw helper under wine so Oodle blobs go through the game's own DLL."""
    work = os.path.dirname(helper)
    dll = os.path.join(work, "oo2core_7_win64.dll")
    if not os.path.exists(dll):
        raise SystemExit(f"copy {game_dir}/oo2core_7_win64.dll next to {helper}")
    lines = []
    for arc, entry, dst in jobs:
        lines.append("\t".join(["Z:" + os.path.abspath(arc).replace("/", "\\"),
                                str(entry["offset"]), str(entry["csize"]), str(entry["usize"]),
                                "Z:" + os.path.abspath(dst).replace("/", "\\")]))
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as handle:
        handle.write("\n".join(lines) + "\n")
        job_file = handle.name
    subprocess.run(["wine", os.path.basename(helper), job_file], cwd=work, check=True)
    os.unlink(job_file)


def patch_fov(data, degrees):
    """Overwrite every RTPC `FOV` float property in an .epe entity file."""
    fov_hash = hash_jenkins("FOV")
    name_hash = hash_jenkins("name")
    out = bytearray(data)
    if out[:4] != b"RTPC":
        raise ValueError("not an RTPC file")
    changed = []

    def visit(offset):
        _, data_offset, prop_count, child_count = struct.unpack_from("<IIHH", out, offset)
        props = {}
        for index in range(prop_count):
            at = data_offset + 9 * index
            key, raw, kind = struct.unpack_from("<IIB", out, at)
            props[key] = (at, raw, kind)
        if fov_hash in props and props[fov_hash][2] == 2:
            at = props[fov_hash][0]
            old = struct.unpack_from("<f", out, at + 4)[0]
            label = ""
            if name_hash in props and props[name_hash][2] == 3:
                start = props[name_hash][1]
                label = out[start:out.index(b"\0", start)].decode("latin1")
            struct.pack_into("<f", out, at + 4, degrees)
            changed.append((label, old))
        children = (data_offset + 9 * prop_count + 3) & ~3
        for index in range(child_count):
            visit(children + 12 * index)

    visit(8)
    return bytes(out), changed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", required=True, help="path to the Just Cause 4 install directory")
    parser.add_argument("--fov", type=float, default=110.0, help="camera FOV in degrees (stock is 50)")
    parser.add_argument("--out", default="dropzone", help="output dropzone directory")
    parser.add_argument("--helper", default=os.path.join(os.path.dirname(__file__), "oodle_dec.exe"),
                        help="path to the compiled Oodle helper")
    args = parser.parse_args()

    found = locate(args.game)
    missing = [name for name in TARGETS if name not in found]
    if missing:
        raise SystemExit("not found in archives: " + ", ".join(missing))

    staged = {}
    jobs = []
    with tempfile.TemporaryDirectory() as scratch:
        for name, (arc, entry) in found.items():
            dst = os.path.join(scratch, name.replace("/", "_"))
            staged[name] = dst
            if entry["ctype"] == 0 or entry["csize"] == entry["usize"]:
                with open(arc, "rb") as handle:
                    handle.seek(entry["offset"])
                    open(dst, "wb").write(handle.read(entry["usize"]))
            elif entry["ctype"] == 4 and entry["block"] == 0:
                jobs.append((arc, entry, dst))
            else:
                raise SystemExit(f"{name}: unsupported compression {entry['ctype']}")
        if jobs:
            oodle_decompress(jobs, args.game, args.helper)

        total = 0
        for name in TARGETS:
            patched, changed = patch_fov(open(staged[name], "rb").read(), args.fov)
            dst = os.path.join(args.out, name)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            open(dst, "wb").write(patched)
            total += len(changed)
            print(f"{len(changed):3d} cameras  {name}")
        print(f"{total} camera FOV values set to {args.fov:g} degrees in {args.out}/")


if __name__ == "__main__":
    sys.exit(main())
