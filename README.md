# FovAlways110 (Just Cause 4)

Dropzone mod that sets every player camera in Just Cause 4 to a 110° field of view instead of the stock 50°. No DLL, no injection, no trainer — it replaces the camera entity data the engine already loads, so the value is fixed from the moment the game boots and never drifts.

## Why

Just Cause 4 ships without an FOV option and the only public alternative is a Cheat Engine table, which has to be re-attached every launch and does not survive under Proton/Wine. Every camera in the game is defined in `rico.epe` with `FOV = 50`, so the clean fix is to edit that value at the source.

## Install

1. Copy the `dropzone` folder into your Just Cause 4 install directory, next to `JustCause4.exe`.
2. Add the VFS arguments to the game's launch options so the engine mounts `dropzone` ahead of the archives (Steam: right click → Properties → Launch Options), keeping `%command%` first:

```
%command% --vfs-fs dropzone --vfs-archive archives_win64/boot_patch --vfs-archive archives_win64/boot_patch/eng --vfs-archive archives_win64/boot --vfs-archive archives_win64/boot/hires --vfs-archive archives_win64/main_patch --vfs-archive archives_win64/main_patch/hires --vfs-archive archives_win64/main_patch/eng --vfs-archive archives_win64/main --vfs-archive archives_win64/main/hires --vfs-archive archives_win64/main/eng --vfs-fs .
```

Add a `--vfs-archive archives_win64/<pack>` and `--vfs-archive archives_win64/<pack>/hires` line for each DLC pack you own (`cp_deathstalker`, `cp_digitaldeluxe`, `cp_neonracer`, `cp_renegade`, …) before the final `--vfs-fs .`, or the game will boot without that content. Non-English installs use their own language folder in place of `eng`.

To uninstall, delete the `dropzone` folder.

## What it changes

| File | Cameras |
| --- | --- |
| `editor/entities/characters/main_characters/rico.epe` | 56 — on foot, wingsuit, parachute, grapple, hoverboard, vehicles, aiming, sniper, death, cutscene framing |
| `editor/entities/weapons/03_mounted/…`, `04_stationary/…` | 8 — minigun, cannon, AA gun, mortar |

Aim and zoom behaviour is untouched: the game applies its zoom adjustments relative to each camera's base FOV, so aiming still narrows the view, just from a wider starting point.

## How it works

Camera entities are RTPC property containers. Each camera node carries a float property `FOV` (Jenkins lookup3 hash `0xFCD59DA7`), which `JustCause4.exe` reads at entity load, multiplies by `0.01745329` (degrees → radians) and stores in the camera object. Every camera in the shipped data uses 50. This mod rewrites those floats in place — the file layout, size and every other property stay byte-identical — and the engine picks the patched file up because `--vfs-fs dropzone` is mounted ahead of the archives.

## Rebuilding for a different FOV

`tools/jc4_fov.py` regenerates `dropzone/` straight from your own installed copy:

```
x86_64-w64-mingw32-gcc -O2 -o tools/oodle_dec.exe tools/oodle_dec.c
cp "<game>/oo2core_7_win64.dll" tools/
python3 tools/jc4_fov.py --game "<game>" --fov 110
```

The helper is only needed to unpack Oodle-compressed archive entries; it calls the game's own `oo2core_7_win64.dll`, under Wine on Linux. Nothing is written to the game directory — copy the generated `dropzone` folder there yourself.

## License

GPL-3.0 — see [LICENSE](LICENSE).
