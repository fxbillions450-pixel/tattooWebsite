# Skin material and desktop rendering release

## Original preserved
Approved source commit: `8e7eb69527565a0ebeaf24a83aa997d23afd4e28`.
Backup branch: `backup/wizards-original-arm-8e7eb69`.
The exact original fragment shader is retained as `originalFragment`. Add `?arm=original` to compare that original material with the current renderer and clean footer; omit the query for the new skin. Neither option changes the mesh, tattoo artwork, camera destinations, or navigation. The backup commit additionally preserves the complete previous website.

## Changes
- Removed the red/purple selectors and custom motion switch from the markup, event handlers and styles. The default red accent remains. Previous/next arrows and section navigation remain available.
- OS `prefers-reduced-motion` is authoritative, including changes in either direction while the website is open. Removed obsolete stored switch preferences; no invisible setting can leave motion stuck off.
- Same arm mesh, with warmer skin/ink response, softer highlights and a generated 256x256 mipmapped texture for subtle stable surface variation. This is a lightweight material pass, not a photogrammetry model or a claim of photorealistic anatomy.
- Desktop drawing density is capped at 1.5 and approximately 4.5 million canvas pixels. Mobile's existing 1.5 density cap and all scroll/touch gesture logic are unchanged. No drawing-buffer resizes are performed during camera travel. HTML text is not downscaled.
- The WebGL drawing buffer is no longer preserved unnecessarily. A settled scene is redrawn when returning to a visible tab, without starting an idle animation loop.
- Hidden markers no longer receive frame-by-frame projections/styles. Panel positioning is cached per mount/resize; repeated panel visibility assignments are idempotent. Camera matrix math reuses buffers and avoids temporary per-frame vector arrays.

## Validation
GitHub Actions run: https://github.com/fxbillions450-pixel/tattooWebsite/actions/runs/37878495593
Verified generated HTML SHA-256: `bc50391184718cb8adfd77aaf3c406ec917480802e29dbd1fc4f978fbb934f2e`.
Root/public generated HTML and the reviewed artifact are identical.
62 renderer/material/layout assertions passed, along with the existing 26 scroll unit cases, 51 motion regression checks, 14 browser navigation scenarios and branding checks. Chromium with real WebGL API execution using SwiftShader software rendering; no physical Windows GPU or phone was tested.

Paired 1760x832 CSS-pixel, device-scale-2 home-to-artist trace:
- Canvas pixels: 4,230,688 to 3,294,720 (22.12% fewer).
- Marker attribute writes: 132 to 2.
- Panel bounding-rectangle reads: 15 to 0.
- Panel attribute writes: 31 to 3.
- Software-rendered median animation-frame interval was approximately 133 ms for BOTH variants; p95 was 550 ms versus 467 ms. This is not proof of 60/120 FPS on a physical desktop. Work reduction is verified; hardware frame rate remains device-dependent.

A separate local numerical comparison of 100 camera matrices and 300 projected points found maximum matrix error below 1e-6 versus the original renderer. The motion solver, scroll router, tattoo generator and mesh remain byte-identical.

References: https://developer.mozilla.org/en-US/docs/Web/API/WebGL_API/WebGL_best_practices and https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/%40media/prefers-reduced-motion
