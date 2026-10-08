# NOIR tattoo website

Approved client-preview concept with the corrected fluid camera transitions.

## Preview

Open `index.html` directly in a modern browser. The website is self-contained and has no network dependencies. The booking form is a demonstration only: it does not submit or create appointments.

## Editable source

`src/` contains the original shell, styles, procedural artwork, raw-WebGL renderer, 3D mesh, motion controller and app navigation. The approved design and motion are preserved.

Run `python tools/build.py` after editing source to rebuild `index.html` and `public/index.html`. Python's standard library is sufficient; the existing mesh is already included.

Regenerating the original mesh, only when intentionally needed, uses `tools/build_mesh.py` with Python 3.13.5, NumPy 2.3.5, SciPy 1.17.0 and scikit-image 0.26.0.

## Approved baseline

Initial approved HTML SHA-256: `0c3feb495cb9d7160e47c0e58b41d4cb02d46d22ee223abc6a45e8d50580be78`.

`vercel.json` sets no-index headers for this client preview. `robots.txt` also discourages crawling; these are not access controls.
