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

The FOV is not reachable through the game's data. The `FOV` property on the camera entities in `rico.epe` is read at entity load and immediately overwritten by the camera framing system; the `CameraSettings.adf` type library baked into `JustCause4.exe` and the hardcoded 50° constructor immediates never reach the renderer — patched to 200, the image is unchanged.

Every camera's projection does go through one 4×4 matrix multiply (`JustCause4.exe+0x75100`, a thunk to the real routine). This mod proxies `oo2core_7_win64.dll`, forwards all 46 Oodle exports to the renamed original, redirects that thunk, and on each call checks whether an operand is a perspective projection — no shear terms, `w` taken from `z`, screen-shaped aspect — and if so rewrites `m00`/`m11` for the requested FOV. UI, shadow and cubemap passes do not match and are left alone.

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
