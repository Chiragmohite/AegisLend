# Chatbot-only 3D assistant refinement — 2026-10-17

## Visual change

New asset: `frontend/public/agents/chatbot-3d.png`.
Consumer: `frontend/src/components/AgentAvatar.tsx`, imported exclusively by `ChatPanel.tsx`.

The prior portrait was reinterpreted using the built-in image-generation tool into a stylized 3D head-and-shoulders bust: Indian male, glasses, swept sculpted dark hair, rounded features, navy suit, white shirt and approachable expression. A first variant was still too realistic; a second targeted generation emphasized sculptural shapes and bust framing and was selected. Original photographs and prior generated assets remain unchanged.

Final generation direction: use the prior character only for broad identity cues; premium animated 3D bust with a larger rounded head, stylized eyes/cheeks, clean simplified materials, chunky sculpted hair, navy blazer and white shirt, subtle studio/rim lighting, no hands or waist, genuine transparent RGBA background, no checkerboard, text or scenery. The final image was visually inspected before integration.

The avatar's container is transparent, and `object-fit: contain` preserves the complete bust on either light or dark surfaces. The dark background used for verification is a test-only header style override; this does not add an application-wide dark theme.

## Actual verification

- PNG inspection: **1254 × 1254, RGBA**.
- Fully transparent pixels: **686,220**. All four corner alpha values are **0**.
- Partially transparent pixels: **885,895**, predominantly alpha 253 (near opaque); fully opaque pixels: **401**. The original generated alpha was retained, not flattened or replaced with a checkerboard.
- The same dimensions and alpha counts were independently checked after loading the image in the real browser through a canvas inspection.
- Actual Playwright/Chromium test of the running React application with the existing isolated synthetic backend: **PASS**.
- Light (`#ffffff`) and dark navy (`#132e43`) header screenshots were visually inspected: no checkerboard, opaque background rectangle or cropping of the bust. Screenshots are internal QA, not bundled customer screenshots.
- Browser assertions passed: no avatar on landing/login/dashboard, correct chatbot PNG loading, transparent container, contain sizing, mobile viewport without horizontal overflow, reduced motion, minimizing/reopening, broken-image fallback and no uncaught page errors.
- `npm test`: **20 passed across 4 files**.
- `npm run build`: **passed** (TypeScript + Vite, 110 modules).
- Backend files compared with pre-refinement hashes: unchanged. No API/authentication/model/migration changes. Backend tests were not rerun for this asset-only refinement; the previous 107-pass report remains historical evidence.

## Reproducible checks

From `frontend` with normal Playwright Chromium installed and the existing Python project environment:

```powershell
npm test
npm run build
npx playwright install chromium
node e2e/avatar.cjs
```

`AEGIS_PYTHON` can select an alternate Python environment. The test starts the existing synthetic-only backend on 8010 and Vite on 5174. It does not connect to the configured application MySQL database. `AEGIS_AVATAR_SCREENSHOTS` optionally selects a local screenshot directory. `AEGIS_BROWSER_EXECUTABLE` and `AEGIS_BROWSER_ARGS` optionally select an existing browser binary and JSON argument array.

In this run, the normal Playwright browser was unavailable, so a temporary `@sparticuz/chromium@153.0.0` test package was installed outside the repository. Its default unpacker failed on an unsupported ownership operation; its packaged binary/fonts were extracted without changing archive ownership. Its initial single-process/font setup crashed, so the successful run used host fonts and ordinary multiprocess headless flags. No application dependency, lockfile, runtime setting or security control was changed. The successful command was `node /tmp/aegis-avatar-browser.mjs`, which configured that temporary browser and invoked `frontend/e2e/avatar.cjs`. This verifies the avatar workflow, not the entire previously blocked full-application E2E suite.

## Files changed in this visual refinement

- Added `frontend/public/agents/chatbot-3d.png`.
- Updated `frontend/src/components/AgentAvatar.tsx`: new asset URL.
- Updated `frontend/src/index.css`: transparent chatbot avatar container and contain sizing.
- Updated `frontend/src/workflows.test.tsx`: expected new asset URL.
- Added `frontend/e2e/avatar.cjs`: real-browser visual integration checks.
- Added this report and linked it from README.

Backend code, APIs, authentication, database schema, migrations and dependency locks are unchanged.
