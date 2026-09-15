#!/usr/bin/env python3
"""Set the camera field of view in Just Cause 4 by patching JustCause4.exe.

The game has no FOV option and ships no camera settings data file: every camera's
framing parameters come from the ADF type library `CameraSettings.adf`, which is
embedded in the executable. This rewrites the FOV defaults in that library.
"""
import argparse
import hashlib
import os
import shutil
import struct
import sys

CAMERA_LIBRARY = b"CameraSettings.adf"
ADF_MAGIC = b" FDA"
VEHICLE_FOV_INSTANCE = "Default:11FB8844_FCD59DA7"
STOCK = {
    "SphericalCoordinateFramingParams.FOV": 50.0,
    "OffsetVectorFramingParams.FOV": 45.0,
}


def find_library(data):
    """Locate the embedded CameraSettings ADF blob by its header comment."""
    at = data.find(CAMERA_LIBRARY)
    while at != -1:
        base = data.rfind(ADF_MAGIC, 0, at)
        if base != -1 and at - base == 0x40:
            return base
        at = data.find(CAMERA_LIBRARY, at + 1)
    raise SystemExit("CameraSettings.adf library not found — unexpected game build")


def read_names(data, base):
    count, offset = struct.unpack_from("<II", data, base + 0x20)
    at = base + offset
    lengths = list(data[at:at + count])
    at += count
    names = []
    for length in lengths:
        names.append(data[at:at + length].decode("latin1"))
        at += length + 1
    return names


def find_fov_fields(data, base):
    """Yield (label, file offset, current value) for every FOV default in the library."""
    names = read_names(data, base)
    type_count, type_offset = struct.unpack_from("<II", data, base + 0x10)
    at = base + type_offset
    fields = []
    for _ in range(type_count):
        name_index, = struct.unpack_from("<Q", data, at + 16)
        member_count, = struct.unpack_from("<I", data, at + 36)
        type_name = names[name_index] if name_index < len(names) else "?"
        member = at + 40
        for _ in range(member_count):
            member_name_index, = struct.unpack_from("<Q", data, member)
            default_kind, = struct.unpack_from("<I", data, member + 20)
            member_name = names[member_name_index] if member_name_index < len(names) else "?"
            if member_name.lower() == "fov" and default_kind == 1:
                value, = struct.unpack_from("<f", data, member + 24)
                fields.append((f"{type_name}.{member_name}", member + 24, value))
            member += 32
        at = member

    instance_count, instance_offset = struct.unpack_from("<II", data, base + 0x08)
    at = base + instance_offset
    for _ in range(instance_count):
        offset, size = struct.unpack_from("<II", data, at + 8)
        name_index, = struct.unpack_from("<Q", data, at + 16)
        if names[name_index] == VEHICLE_FOV_INSTANCE:
            for index in range(size // 4):
                where = base + offset + 4 * index
                value, = struct.unpack_from("<f", data, where)
                fields.append((f"GenericVehicleCamera.FOV[{index}]", where, value))
        at += 24
    return fields


def backup_path(exe):
    return exe + ".orig"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", required=True, help="Just Cause 4 install directory")
    parser.add_argument("--fov", type=float, default=110.0, help="field of view in degrees (stock is 50)")
    parser.add_argument("--revert", action="store_true", help="restore the original executable")
    parser.add_argument("--show", action="store_true", help="print the current values and exit")
    args = parser.parse_args()

    exe = os.path.join(args.game, "JustCause4.exe")
    if not os.path.exists(exe):
        raise SystemExit(f"{exe} not found")

    if args.revert:
        if not os.path.exists(backup_path(exe)):
            raise SystemExit("no backup to restore")
        shutil.copyfile(backup_path(exe), exe)
        print("restored the original JustCause4.exe")
        return

    data = bytearray(open(exe, "rb").read())
    base = find_library(data)
    fields = find_fov_fields(data, base)

    if args.show:
        for label, where, value in fields:
            print(f"{label:38s} {value:g} @ {where:#x}")
        return

    if not 1.0 <= args.fov <= 179.0:
        raise SystemExit("--fov must be between 1 and 179 degrees")

    for label, _, value in fields:
        expected = STOCK.get(label)
        if expected is not None and abs(value - expected) > 1e-3 and not os.path.exists(backup_path(exe)):
            raise SystemExit(f"{label} is {value:g}, expected the stock {expected:g} — refusing to patch")

    if not os.path.exists(backup_path(exe)):
        shutil.copyfile(exe, backup_path(exe))
        print(f"backed up the original to {os.path.basename(backup_path(exe))}")

    for label, where, value in fields:
        struct.pack_into("<f", data, where, args.fov)
        print(f"{label:38s} {value:g} -> {args.fov:g}")
    open(exe, "wb").write(bytes(data))
    print(f"patched {len(fields)} camera FOV defaults in JustCause4.exe")


if __name__ == "__main__":
    sys.exit(main())
