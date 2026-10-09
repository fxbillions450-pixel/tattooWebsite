# Wizards Tattoos: four audit corrections

Baseline: `673fbfe36f825ed878c0fa13662a3d9bb8e68059`.

- WIZ-01: below 481 CSS pixels tall, fit the application to its existing stable small viewport, reserve header/footer space, and keep the panel itself scrollable. Accommodate safe-area insets. Portrait and standard-height desktop rules are unchanged; no dynamic-viewport or virtual-keyboard camera-resizing loop was added.
- WIZ-02: dismiss open artwork on section/history navigation, then focus the target section control without scrolling the document. Ordinary X/Escape closure restores only a connected, visible gallery opener; a queued old close event cannot steal focus from a newly opened dialog.
- WIZ-03: change only the generated gallery image footer to `WIZARDS TATTOOS / ORIGINAL STUDY`. Keep sleeve texture generation and the illustration regions unchanged.
- WIZ-04: validate trimmed name and idea before showing a demo request. Custom validity clears as the user corrects the field. Preview uses normalized text; Edit retains the unmodified draft. Inputs still render as text, never HTML. This does not enable real bookings.

Only `src/app.js`, `src/artwork.js`, and `src/styles.css` require runtime changes. The arm mesh, material/renderer, camera solver, scroll router, logo, shell and build script are unchanged. Original arm fallback and backup remain available.

Regression command: `python3 tests/audit_cleanup.py` (Playwright 1.57.0, Pillow 11.3.0). Supply `WIZARDS_BASELINE_HTML` for home visual comparison at five normal screen sizes, exact sleeve texture parity and exact gallery illustration-region parity. `WIZARDS_REQUIRE_WEBGL=1` makes a missing or lost WebGL context fail explicitly. `WIZARDS_AUDIT_URL` runs the same behavioral checks on a public deployment. Existing scroll, camera and branding tests must also pass.

The home screenshot comparison asserts identical layout geometry. It records every image/difference and permits at most one RGB intensity level of rounding in at most 0.01% of pixels. This follows inspection of a 1760x832 CI comparison with 59 heading-edge pixels differing by only 1/255; the other four sizes were pixel-identical. This tolerance does not permit moved text, modified arm geometry, missing objects or perceptible color changes. It is a visual-regression check, not a physical-device FPS measurement.

References: https://developer.mozilla.org/en-US/docs/Web/API/HTMLDialogElement/close and https://developer.mozilla.org/en-US/docs/Web/API/HTMLInputElement/setCustomValidity and https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Values/length
