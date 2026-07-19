# Sprint 20 Remaining Work

Sprint 20 implementation is complete and locally committed, but these follow-up items remain for final acceptance or future hardening.

## Manual Acceptance Still Pending

- Run the full live browser acceptance flow with backend and frontend servers running.
- Log in through the UI and open an editable project layout.
- Make several canvas edits and confirm the editor remains responsive.
- Simulate an expired access token during active editing.
- Trigger auto-save and confirm the session refreshes without redirecting to login.
- Trigger manual Save Layout and confirm the save completes once.
- Confirm only one intended named version exists after manual save.
- Force refresh-token failure and confirm the app logs out safely.
- Confirm unsaved in-memory work is not incorrectly marked as saved.
- Confirm no infinite loading state or request loop occurs.

## Security Hardening Follow-Up

- Refresh tokens are still stored in `localStorage` to match the current app architecture.
- Move refresh tokens to secure `HttpOnly` cookies in a future hardening sprint.
- Revisit CSRF protection when refresh-token cookies are introduced.
- Consider server-side refresh-token reuse detection for stricter rotation abuse handling.

## CI Follow-Up

- The new GitHub Actions workflow has not been observed on GitHub yet because no push or PR was created.
- Verify the backend dependency install succeeds in CI, especially the pinned Scrapling Git dependency.
- If CI install time is too high, consider safe dependency caching or a dedicated test requirements file.

## Non-Blocking Warnings Observed

- Frontend build still warns that some chunks are larger than 500 kB after minification.
- Vite reports the CJS Node API deprecation warning during tests/build.
- Node warns that `frontend/postcss.config.js` is reparsed as an ES module because `package.json` does not declare `"type": "module"`.
- Backend tests emit a `python_multipart` pending deprecation warning through Starlette.
- React Router tests emit v7 future-flag warnings.

## Repository Follow-Up

- Sprint 20 branch remains local: `sprint-20/reliable-sessions-save-safety-ci`.
- No push or PR has been created.
- Unrelated untracked local items remain outside the sprint commits: `.thumbnail`, `screenshots/`, and `uploads/`.
