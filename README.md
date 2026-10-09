# Wizards Tattoos

Client-preview concept with the approved 3D tattoo sleeve, fluid camera transitions and continuous section scrolling.

## Build and preview

Run `python3 tools/build.py` (or `python tools/build.py` on Windows) **before opening or sharing** `index.html` or `public/index.html`. These are generated snapshots; `src/` and the checked-in logo asset are the current source of truth. The build uses only Python's standard library and produces a self-contained HTML file with no external assets or network dependencies.

Open the freshly built `index.html` in a modern browser. The booking form remains a demonstration: it does not submit or create appointments.

## Branding

The website is named **Wizards Tattoos**, as requested. The original black-and-white profile logo from https://www.instagram.com/wizardstattoos/ is saved in `assets/wizards-instagram-logo.jpg`. Instagram supplies a 150 x 150 image; the header uses it at a compact display size. The logo is embedded in the built HTML instead of hotlinked to Instagram. See `docs/wizards-branding.md` for its provenance and checksum.

`src/brand.css` adds the brand-specific header and loading-screen layouts, including compact mobile sizes. The original stylesheet, renderer, mesh, artwork, motion and scroll controller are unchanged by the branding update. Internal `NOIR` JavaScript identifiers are retained to avoid needless interaction regressions; they are not the website's visible name.

## Editable source

`src/` contains the shell, styles, procedural artwork, raw-WebGL renderer, 3D mesh, motion controller and application navigation. Rebuild after editing source.

Regenerating the original mesh, only when intentionally needed, uses `tools/build_mesh.py` with Python 3.13.5, NumPy 2.3.5, SciPy 1.17.0 and scikit-image 0.26.0. Ordinary website builds reuse the committed mesh and require none of these dependencies.

## Automatic Vercel deployments

Vercel's native Git integration builds source changes using the checked-in `vercel.json`:

| Setting | Value |
| --- | --- |
| Framework | Other (`null`) |
| Build command | `python3 tools/build.py` |
| Output directory | `public` |
| Install command | Empty |

Keep the repository root as Vercel's Root Directory. Pushes to the configured production branch (`main`) update the existing production URL; other branches create separate previews. A local commit must be pushed to GitHub before deployment. A push containing several commits deploys the latest state.

No additional deployment workflow or Vercel token is needed. Vercel project permissions, repository linkage and commit-author authorization still apply. Only `public/` is served. The build always regenerates the HTML so an older generated snapshot is not served in place of current source.

Official references: https://vercel.com/docs/git and https://vercel.com/docs/project-configuration/git-configuration

## Verification

After building, run `node --test tests/*.test.cjs`, `node tools/test_motion.cjs` and `python3 tests/browser_scroll.py` with Playwright/Chromium installed. `python3 tests/branding.py` verifies the saved logo, visible name, mobile menus and header fit at seven viewport sizes. Set `REQUIRE_WEBGL=1` when a test must fail rather than use the no-WebGL fallback. Browser emulation is not physical-phone testing.

## Historical approved baseline

Initial approved HTML SHA-256: `0c3feb495cb9d7160e47c0e58b41d4cb02d46d22ee223abc6a45e8d50580be78`. This identifies the original design, not subsequent scroll or branding builds.

`vercel.json` sets no-index headers for this client preview. `robots.txt` also discourages crawling; neither is an access control.
