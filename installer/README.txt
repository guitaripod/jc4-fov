FovAlways - Just Cause 4 field of view      version @VERSION@
============================================================

Just Cause 4 renders at about 52 degrees vertical (82 horizontal at 16:9) and
has no FOV setting. This mod sets it to whatever you want - 100 degrees
vertical (139 horizontal) out of the box.


INSTALL - WINDOWS
-----------------
Copy install.bat, uninstall.bat, oo2core_7_win64.dll and jc4_fov.txt into your
Just Cause 4 folder (the one with JustCause4.exe), then double click
install.bat. You can also drag the game folder onto install.bat from anywhere.

Typical folder:
  C:\Program Files (x86)\Steam\steamapps\common\Just Cause 4


INSTALL - LINUX / STEAM DECK
----------------------------
  ./jc4fov.sh install

It finds the game in your Steam libraries. Pass the folder if it cannot:
  ./jc4fov.sh install "/path/to/steamapps/common/Just Cause 4"


CHANGING THE FOV
----------------
Edit jc4_fov.txt in the game folder - one number, the VERTICAL field of view in
degrees, 1 to 179. It is read when the game starts. On Linux you can also run
  ./jc4fov.sh fov 120

At 16:9 the horizontal field of view works out as:

  vertical  50 (about stock)  ->  horizontal  79
  vertical  75                ->  horizontal 106
  vertical  90                ->  horizontal 121
  vertical 100  (default)     ->  horizontal 139
  vertical 130                ->  horizontal 154

Above roughly 140 vertical the edges of the screen stretch a lot.


UNINSTALL
---------
Windows: double click uninstall.bat.  Linux: ./jc4fov.sh uninstall
Verifying the game files in Steam also restores the stock DLL, which disables
the mod until you run the installer again.


HOW IT WORKS
------------
The game's own FOV values cannot be reached from the outside: the FOV property
on the camera entities is overwritten by the camera framing system every update,
and the values baked into the executable never reach the renderer. What the
renderer does read is a single field on each render view, so the mod proxies
oo2core_7_win64.dll (all Oodle calls are forwarded to the renamed original),
redirects the engine's view setup routine, and writes your FOV into that field
before the engine builds anything from it. The projection, the frustum and the
rays the sky and cloud passes use all come from that one value, so the whole
image stays consistent. Cubemap captures and shadow cascades keep their own FOV.

jc4_fov.log in the game folder records whether the hook installed.

Nothing in the game is modified: the mod only adds files, and works on Windows
and on Linux/Proton.


SOURCE AND ISSUES
-----------------
https://github.com/guitaripod/jc4-fov   (GPL-3.0)
