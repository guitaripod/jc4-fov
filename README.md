# FovAlways110 (Just Cause 4)

Just Cause 4 has no field-of-view option and its cameras sit at a very tight 50°. This sets every gameplay camera to 110° (or any value you pass) by patching the camera defaults inside `JustCause4.exe`.

## Why patch the executable

The camera entities in `rico.epe` do carry an `FOV` property, and the engine does read it — but it is only the initial value, overwritten from the camera framing system on the next update, so a dropzone data mod has no visible effect. The framing parameters themselves ship in no data file at all: they live in the ADF type library `CameraSettings.adf`, which is embedded in the executable, as the default values of `SphericalCoordinateFramingParams` (on foot, wingsuit, parachute, grapple, everything third person), `OffsetVectorFramingParams` and `GenericVehicleCamera`. Those defaults are the only place the FOV exists, so that is what this patches.

## Use

```
python3 tools/jc4_fov.py --game "<path to Just Cause 4>" --fov 110
```

- The original executable is copied to `JustCause4.exe.orig` on the first run.
- `--show` prints the current values, `--revert` restores the backup.
- Steam's *Verify integrity of game files* also restores the stock executable.
- The patch refuses to run if the values are not the stock 50 / 45 / 45 / 60, so it cannot be applied twice or to an unexpected build.

Values written (all set to the requested FOV in degrees):

| Field | Stock | Cameras it drives |
| --- | --- | --- |
| `SphericalCoordinateFramingParams.FOV` | 50 | third-person gameplay cameras |
| `OffsetVectorFramingParams.FOV` | 45 | offset-framed cameras |
| `GenericVehicleCamera.FOV[0..1]` | 45, 60 | vehicle cameras (speed-blended range) |

## Notes

Aiming and scope zoom stay relative: the game applies `FOVZoomAdjustment` on top of the camera FOV, so aiming still narrows the view from the wider base. Cutscenes use their own cameras and are untouched.

## License

GPL-3.0 — see [LICENSE](LICENSE).
