# openhost-synapse-admin

[synapse-admin](https://github.com/Awesome-Technologies/synapse-admin) packaged
as an [OpenHost](https://github.com/imbue-openhost/openhost) app: an admin UI
for [Matrix Synapse](https://github.com/element-hq/synapse) homeservers (manage
users, rooms, media, reports, ...).

The app is a fully static SPA. The Dockerfile downloads the pinned upstream
release tarball (sha256-verified, prebuilt by upstream with a relative base
path) and serves it with nginx on port 8080. There is no backend and no
persistent data; everything runs client-side in the browser, talking directly
to the Synapse homeserver's admin API.

Access is gated by the OpenHost router (no `public_paths`). Once logged in to
OpenHost, sign in on the synapse-admin login page with an admin account on the
target homeserver (or an access token). Note that the *browser* talks to the
homeserver, so the homeserver must be reachable from wherever you're browsing,
and its CORS settings must allow it (Synapse's defaults do).

## upgrading synapse-admin

Bump `SYNAPSE_ADMIN_VERSION` and `SYNAPSE_ADMIN_SHA256` in the `Dockerfile`
(sha256 of the new release tarball), and the versions in `openhost.toml` and
`pyproject.toml`.

## remaining work

- `test_login_page_renders` is marked `xfail(strict=False)`: react-admin
  sometimes stalls after its initial checkAuth/logout and never mounts the
  login form (all assets load with 200s, no JS errors, no failed requests; the
  page stays on the static loader shell). Reproducible against upstream's own
  docker image, and it never renders at all under playwright's default
  chromium-headless-shell (hence `--browser-channel chromium` in pytest
  addopts). Root cause not yet found — likely an upstream react-admin 5 /
  react-router 7 race.
- The test harness intermittently fails with "full app did not come up after
  /setup" (a 60s poll of the router's own dashboard, before the app deploys);
  rerunning passes. Needs investigation in the harness, not this repo.
- Upstream release tarballs ship `index.html` with the `__SYNAPSE_ADMIN_VERSION__`
  vite placeholder unsubstituted, which throws in the browser; the Dockerfile
  patches it with sed. Worth reporting upstream.
- Not yet deployed to a real OpenHost instance.

## development

```bash
just setup   # install deps, pre-commit hooks, and the playwright chromium browser
just run     # build the image and serve locally on http://localhost:8080
just test    # run the test suite
just check   # lint, format, typecheck
```

Python here is test-only tooling, managed with [uv](https://docs.astral.sh/uv/).

`just test` uses the OpenHost test harness (the `openhost[test-harness]` package),
which builds the Dockerfile and runs the app under **podman** (so podman must be
running on the host) fronted by the real OpenHost router. `stack.url` requires
owner auth (use `stack.owner_session` for requests, or `stack.playwright_login(page)`
for browser tests); `stack.app_url` hits the container directly. See `tests/` for the
`stack` fixture.
