# Continuous section navigation

The earlier wheel controller used a 650 ms repeat gate and a consumed-stroke latch with peak-relative strength checks. It could discard continued input even though the camera already supported interruptible retargeting. This was input policy, not a requirement to finish the WebGL animation or a demonstrated hosting limitation.

Scene scrolling now uses accumulated distance: 36 normalized CSS pixels for the first destination and 96 for subsequent destinations in the same stroke. There is no repeat timer, landing check, strength-relative filter, or delayed navigation queue. A strong sustained flick intentionally may cross more than one section. Tiny residual deltas do not each become full section changes. Reversing clears accumulated forward intent and immediately redirects after a 36-pixel intent threshold. Long touch drags can also pass multiple sections without lifting the finger.

Readable panel content retains native scrolling. A gesture that begins by reading stays owned by that content; a fresh outward gesture at its boundary navigates. During camera travel an inert incoming panel cannot steal scene input. Editable controls, browser zoom, horizontal gestures, open menus and dialogs are excluded.

No changes were made to app camera choreography, the motion solver, renderer, mesh, artwork, style sheet, or destination poses. The standalone root and public HTML builds must match, so hosted and downloaded copies use the same input code.

Run `node --test tests/*.test.cjs`, `node tools/test_motion.cjs`, and `python tests/browser_scroll.py` (Playwright 1.57.0 + Chromium). Browser tests require WebGL and cover actual wheel/touch routing, mid-transition continuation/reversal, native content, browser history, and local file vs HTTP. The previous one-long-flick-must-never-cross-multiple-sections assertion was deliberately replaced to reflect the user's requested free navigation behavior; it is not an unchanged acceptance criterion.
