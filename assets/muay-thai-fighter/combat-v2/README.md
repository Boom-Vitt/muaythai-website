# Akhani combat combo — 2026-09-12

Original ten-strike choreography on the project's existing human Akhani rig:
jab → cross → jab → cross → left hook → right uppercut → left hook → cross →
right knee → jumping punch → airborne guard → cushioned landing.
Low staggered guard, fast extensions, brief impact holds, torso/hip counterrotation,
weight transfer and rear forefoot pivots, with stylized fighting-game hang time.
No external motion clip or paid generation is used to author this Blender scene.

- Editable source: `akhani-combat.blend`; preserves all earlier assets.
- Website: `../../../web-assets/akhani-combat.glb`, `akhani-combat-poster.png`,
  `combat-preview.mp4`, `combat-poster.jpg`.
- Preview: 300 PNG frames, 1280×720, 30 fps, ten seconds, H.264 MP4 with no audio.
- GLB: character only, 22 joints, one `Combat_Combo` animation, exactly 0–10 seconds.
- Impact frames: 24, 35, 48, 62, 78, 95, 113, 132, 175, 215.
  Airborne guard: 240; landing: 265. Video/GLB time is `(frame - 1) / 30`.
- Frame 301 repeats frame 1 for the exact GLB loop; MP4 renders frames 1–300.
- Earlier completed six-second version is retained locally in `draft-six-second/`.

From the project root, author, inspect and export:

```sh
/Applications/Blender.app/Contents/MacOS/Blender --background --python-exit-code 1 --python scripts/improve_boxing.py
```

The script checks every evaluated frame for finite mesh coordinates, foot clearance,
camera bounds and exact loop closure, plus the exported animation name and clock.
It writes `validation.json` and seven review stills. Append `-- --render` to render
the full sequence instead of stills, then encode:

```sh
ffmpeg -y -framerate 30 -start_number 1 -i assets/muay-thai-fighter/combat-v2/frames/frame_%04d.png -frames:v 300 -c:v libx264 -crf 18 -preset medium -pix_fmt yuv420p -movflags +faststart -an web-assets/combat-preview.mp4
ffmpeg -v error -i web-assets/combat-preview.mp4 -f null -
```

Native checks passed on 2026-09-12: all 301 frames, ~2 mm planted sole clearance,
zero loop error, >2.3% conservative camera margin, exact glTF 0–10 second timing.
At the jumping punch the soles clear the floor by 65.5/76.5 cm; airborne guard
clears 48.5 cm; landing returns both soles to 2 mm. Each frame's expected contact
state is checked, so airborne poses are not incorrectly clamped to the floor.
Full-size poses were visually reviewed; jab extension, high uppercut, compact
guard and shorts weights were refined from that review. This is a stylized authored sculpt
and animation, not motion capture or a high-detail game character.

Final MP4 probing and complete decode passed: 300 frames, 10.000 seconds,
1280×720 H.264/yuv420p, 823,025 bytes. The contact sheet was extracted from that
encoded MP4 and inspected. Lead-foot XY drift during 229 planted frames was
0.285 micrometers (numerical noise). All metrics are in `validation.json`.
