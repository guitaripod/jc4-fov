# JC4 FOV

Field of view mod for Just Cause 4. The game renders at roughly 52° vertical (82° horizontal at 16:9) and has no FOV option; this sets it to any value you want — 100° vertical by default — for every camera, without modifying a single game file.

[Nexus Mods page](https://www.nexusmods.com/justcause4/mods/29)

## Install

Grab the archive from [releases](https://github.com/guitaripod/jc4-fov/releases), then:

- **Windows** — copy its contents into the folder with `JustCause4.exe` and run `install.bat`
- **Linux / Steam Deck** — `./jc4fov.sh install` (finds the game in your Steam libraries)

Set the vertical FOV in `jc4_fov.txt` (1–179 degrees, read at game start), or `./jc4fov.sh fov 120`. At 16:9: 75 → 106° horizontal, 100 → 139°, 130 → 154°.

Uninstall with `uninstall.bat` or `./jc4fov.sh uninstall`.

## How it works

The FOV is not reachable through the game's data. The `FOV` property on the camera entities in `rico.epe` is read at entity load and immediately overwritten by the camera framing system; the `CameraSettings.adf` type library baked into `JustCause4.exe` and the hardcoded constructor immediates never reach the renderer — patched to 200, the image is unchanged.

What does reach the renderer is one float on the render view. `JustCause4.exe+0x753F0` thunks to the routine that prepares a view for rendering: it reads the vertical FOV in radians from `view+0x588` and the aspect ratio from `view+0x5A4`, builds the projection into `view+0x294` — symmetric, off-centre when the frame is jittered, orthographic for shadow cascades — and then derives the frustum from that same field again.

This mod proxies `oo2core_7_win64.dll`, forwards all 46 Oodle exports to the renamed original, redirects that thunk, and writes the requested FOV into `view+0x588` before the engine reads it. Projection, frustum and the view rays that the sky and volumetric cloud passes march along all come from that one number, so they stay consistent — rewriting the projection matrix further downstream does not, which leaves the sky drawn at the stock FOV and sliding against the world. Square and orthographic views — cubemap captures, shadow cascades — keep their own FOV.

## Build

```
./build.sh              # oo2core_7_win64.dll, needs mingw-w64
./package.sh 1.1.0      # dist/JC4-FovAlways-1.1.0.zip
```

## Releasing

Publishing a GitHub release builds the archive, attaches it, and uploads it to the Nexus mod page through the [official upload action](https://github.com/Nexus-Mods/upload-action) (`NEXUSMODS_API_KEY` repository secret, mod 29 / file 55). The release body becomes the Nexus changelog.

```
gh release create v1.2.0 --title "1.2.0" --notes "what changed"
```

`docs/nexus-description.bbcode` is the mod page description, kept in sync by hand — Nexus has no API for page text.

## License

GPL-3.0 — see [LICENSE](LICENSE).
