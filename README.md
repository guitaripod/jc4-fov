# JC4 FOV

Just Cause 4 has no field-of-view option; it renders at roughly 52° vertical in gameplay (~82° horizontal at 16:9). This sets the vertical FOV to whatever you ask for — 130° by default — by intercepting the engine's perspective matrices at runtime.

## How it works

The FOV is not authored anywhere you can reach from the outside. The `FOV` property on the camera entities in `rico.epe` is read at entity load but immediately overwritten by the camera framing system; the `CameraSettings.adf` type library baked into `JustCause4.exe` and the hardcoded 50° constructor immediates have no effect on the rendered image either — patching all of them to 200 changes nothing on screen.

What does work is the last common choke point. Every camera's projection goes through one 4×4 matrix multiply (`JustCause4.exe+0x75100`, a thunk to the real routine). This mod proxies `oo2core_7_win64.dll`, redirects that thunk, and on each call checks whether either operand is a perspective projection — no shear terms, `w` taken from `z` — and if so rewrites `m00`/`m11` for the requested FOV, preserving the aspect ratio. UI and other passes are untouched because their matrices do not match.

## Install

```
./build.sh
cd "<Just Cause 4>"
mv oo2core_7_win64.dll oo2core_7_win64_real.dll
cp <this repo>/oo2core_7_win64.dll .
echo 130 > jc4_fov.txt
```

The proxy forwards all 46 Oodle exports to `oo2core_7_win64_real.dll`, so decompression is unaffected. `jc4_fov.txt` holds the vertical FOV in degrees (1–179) and is read once at startup; `jc4_fov.log` records the hook result and the first few matrices it rewrote.

At 16:9, vertical 130° is about 154° horizontal. Stock is ~52° vertical / 82° horizontal.

## Uninstall

Delete `oo2core_7_win64.dll` and rename `oo2core_7_win64_real.dll` back. Steam's *Verify integrity of game files* also restores the stock Oodle DLL, which disables the mod.

## License

GPL-3.0 — see [LICENSE](LICENSE).
