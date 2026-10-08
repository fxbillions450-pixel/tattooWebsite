# NOIR tattoo website

Approved client-preview concept with the corrected fluid camera transitions.

## Preview

Open `index.html` directly in a modern browser. The website is self-contained and has no network dependencies. The booking form is a demonstration only: it does not submit or create appointments.

## Editable source

`src/` contains the original shell, styles, procedural artwork, raw-WebGL renderer, 3D mesh, motion controller and app navigation. The approved design and motion are preserved.

Run `python tools/build.py` after editing source to rebuild `index.html` and `public/index.html`. Python's standard library is sufficient; the existing mesh is already included.

Regenerating the original mesh, only when intentionally needed, uses `tools/build_mesh.py` with Python 3.13.5, NumPy 2.3.5, SciPy 1.17.0 and scikit-image 0.26.0.

## Automatic Vercel deployments

The repository configuration is ready for Vercel's native Git integration. It does not create or link a Vercel project by itself. The repository must first be imported into the personal Vercel workspace, with `main` selected as the Production Branch.

After that one-time connection:

- Pushes and merges to `main` build the latest commit and update the project's stable production URL.
- Other branches receive separate preview deployments by default, without replacing the production URL.
- A commit saved only on your computer does not deploy until it is pushed to GitHub. A push containing several commits deploys its latest state, not a separate website for every intermediate commit.

The checked-in `vercel.json` enables Git deployments and sets:

| Setting | Value |
| --- | --- |
| Framework | Other (`null`) |
| Build command | `python3 tools/build.py` |
| Output directory | `public` |
| Install command | Empty; no dependency installation required |

Keep the repository root as Vercel's Root Directory. The build command regenerates the standalone HTML from `src/` on every deployment, so edits are not lost behind a stale committed `public/index.html`. The original mesh is reused; no mesh regeneration or scientific Python dependencies run during deployment. Only `public/` is served.

No additional GitHub Actions deployment workflow, deploy hook, or Vercel token is required for the native Git integration. Vercel permissions, project connection, and commit-author authorization still apply. Configuration readiness is not proof of a successful hosted deployment.

Official references: https://vercel.com/docs/git and https://vercel.com/docs/project-configuration/git-configuration

## Approved baseline

Initial approved HTML SHA-256: `0c3feb495cb9d7160e47c0e58b41d4cb02d46d22ee223abc6a45e8d50580be78`.

The automatic-build command was tested against source files matching GitHub's blob hashes and reproduced this exact baseline. A temporary source-edit test also confirmed that source changes reach the generated `public/index.html`; the test edit was not committed.

`vercel.json` sets no-index headers for this client preview. `robots.txt` also discourages crawling; these are not access controls.
