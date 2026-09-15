#!/usr/bin/env bash
# Installs, removes or reconfigures the Just Cause 4 FOV mod (Linux / Steam Proton).
set -euo pipefail

usage() {
  cat >&2 <<USAGE
usage: $0 install [game-dir]     install the mod (auto-detects a Steam install)
       $0 uninstall [game-dir]   restore the stock Oodle DLL
       $0 fov <degrees> [dir]    change the vertical FOV (1-179)
USAGE
  exit 1
}

find_game() {
  local libraries=("$HOME/.steam/steam" "$HOME/.local/share/Steam")
  local vdf="$HOME/.steam/steam/steamapps/libraryfolders.vdf"
  if [[ -f $vdf ]]; then
    while read -r path; do libraries+=("$path"); done < <(grep -oP '"path"\s+"\K[^"]+' "$vdf" || true)
  fi
  for lib in "${libraries[@]}"; do
    if [[ -f "$lib/steamapps/common/Just Cause 4/JustCause4.exe" ]]; then
      echo "$lib/steamapps/common/Just Cause 4"
      return 0
    fi
  done
  return 1
}

resolve_game() {
  local given="${1:-}"
  [[ -n $given ]] || given="$(find_game || true)"
  if [[ -z $given || ! -f "$given/JustCause4.exe" ]]; then
    echo "Could not find Just Cause 4 - pass the folder containing JustCause4.exe" >&2
    exit 1
  fi
  echo "$given"
}

cmd_install() {
  local game here
  game="$(resolve_game "${1:-}")"
  here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  if [[ ! -f "$game/oo2core_7_win64_real.dll" ]]; then
    if [[ $(stat -c%s "$game/oo2core_7_win64.dll") -lt 500000 ]]; then
      echo "oo2core_7_win64.dll is already a proxy but the original is missing - verify the game files in Steam first" >&2
      exit 1
    fi
    mv "$game/oo2core_7_win64.dll" "$game/oo2core_7_win64_real.dll"
  fi
  cp "$here/oo2core_7_win64.dll" "$game/"
  [[ -f "$game/jc4_fov.txt" ]] || cp "$here/jc4_fov.txt" "$game/"
  echo "installed into $game (FOV $(cat "$game/jc4_fov.txt"))"
}

cmd_uninstall() {
  local game
  game="$(resolve_game "${1:-}")"
  [[ -f "$game/oo2core_7_win64_real.dll" ]] || { echo "not installed in $game" >&2; exit 1; }
  rm -f "$game/oo2core_7_win64.dll" "$game/jc4_fov.txt" "$game/jc4_fov.log"
  mv "$game/oo2core_7_win64_real.dll" "$game/oo2core_7_win64.dll"
  echo "uninstalled from $game"
}

cmd_fov() {
  local value="${1:-}" game
  [[ $value =~ ^[0-9]+$ ]] && (( value >= 1 && value <= 179 )) || usage
  game="$(resolve_game "${2:-}")"
  echo "$value" > "$game/jc4_fov.txt"
  echo "vertical FOV set to $value - restart the game"
}

case "${1:-}" in
  install)   shift; cmd_install "$@" ;;
  uninstall) shift; cmd_uninstall "$@" ;;
  fov)       shift; cmd_fov "$@" ;;
  *)         usage ;;
esac
