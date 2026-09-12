# Akhani cinematic animation — 2026-09-12

The Blender clip is a **motion reference only**. Character appearance, costume,
rendering style and the fantasy Thai arena come from `akhani-keyframe.png`,
created with built-in Imagegen. Exact image prompt: `image-prompt.txt`;
full cinematic prompt: `prompt.txt`.

## Completed generation

- Runtime: existing `antirez/h3.c` `8974cc0`, original MiniMax H3 Ref2VA,
  Apple Silicon, seed `38471`, 20 steps, 50 layers, SSD streaming.
- Appearance/environment input: `--ref-image akhani-keyframe.png`.
- Movement input: `--ref-silent-video motion-only-reference.mp4`, a grayscale
  224×128 derivative of the actual Blender sequence, 243 frames at 24 fps
  including the final hold. Its mannequin, clothes, materials and studio are
  explicitly excluded from the target appearance.
- Full native generation completed with exit code 0: 1024×576,
  243 frames / 10.125 seconds, with AAC audio, 4,493,991 bytes.
- Website output: `../../../web-assets/h3-cinematic-bg.mp4`, H.264,
  1024×576, 24 fps, 240 frames / exactly 10 seconds, no audio,
  3,360,307 bytes. Encoding removes the final three-frame hold and audio.
- Website poster: `../../../web-assets/akhani-cinematic-poster.jpg`, derived
  from the new character keyframe.

## Validation and limits

The native and website videos both passed full decode. Review of 30 sampled
frames plus 24 frames around the jump confirmed the new image-derived hero
and temple environment, distinct punches, a leg raise/kick variation,
clear airborne guard and landing. H3 reinterprets the authored knee as a
leg raise/kick; it does not replicate every authored strike or timestamp,
and the loop is not pixel-exact. The website's pose controls synchronize the
interactive GLB with the Blender clip, not with this freely staged cinematic.

`node scripts/check_website.cjs` passed on 2026-09-12, including the final
video's dimensions, duration, frame count, rate and absence of audio.
Final browser QA passed at 1440×900 and 390×844: actual ten-second cinematic
playback, dialog/background pause and resume, all six synchronized model/Blender
pose seeks, mobile menu, no horizontal overflow and no console warnings/errors.
Safe validation details are recorded in `validation.json`.

## Provenance and local intermediates

Public provenance comprises `akhani-keyframe.png`, `image-prompt.txt`,
`prompt.txt`, `preview-prompt.txt`, `motion-only-reference.mp4` and
`validation.json`, alongside this README. The runtime website needs only its
encoded media and poster in `web-assets/`.

The earlier style preview (512×288, 73 frames / 3.041667 seconds) passed
full decode and six sampled visual checks before full generation. Its native
video, the full native output, contact sheets and machine-specific generation
records remain local intermediates; they are not required public files.
The previously rejected `../h3-combat/` candidate is superseded and is not
part of the final cinematic presentation.
