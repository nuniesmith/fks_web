# Visual Regression Seed

This directory seeds future visual regression tests. Suggested next steps:

1. Install Playwright: `npm i -D @playwright/test` and run `npx playwright install --with-deps`.
2. Create a minimal page that renders `<AppNavigation />` with mocked providers.
3. Capture baseline screenshot: `npx playwright test --update-snapshots`.
4. Integrate into CI (only run on PRs touching `src/features/navigation/**`).

For now, React/Vitest snapshot tests cover structural regressions; migrate to pixel diffs when UI stabilizes.
