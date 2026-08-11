# openhost-synapse-admin

[synapse-admin](https://github.com/Awesome-Technologies/synapse-admin) packaged
as an [OpenHost](https://github.com/imbue-openhost/openhost) app: an admin UI
for [Matrix Synapse](https://github.com/element-hq/synapse) homeservers (manage
users, rooms, media, reports, ...).

Upstream lives in `synapse-admin/` as a **git subtree**, lightly forked and built
from source. A small Python (Litestar) server serves the build and owns the one
piece of state that isn't upstream's: the Matrix session.

## the fork: the session lives on the server

Stock synapse-admin keeps the session (homeserver URL, access token, user id,
device id) in the browser's `localStorage`, so every browser needs its own login.
Here it lives on the OpenHost instance instead, at
`$OPENHOST_APP_DATA_DIR/session.json` (mode 0600) — log in once, and any browser
that reaches the app is already logged in.

Upstream funnels every session read and write through a one-line seam,
`synapse-admin/src/storage.ts` (`const storage = localStorage`). The fork
replaces that module with a server-backed store of the same shape, so no call
site changes:

- reads stay **synchronous** (they happen during render) by serving from an
  in-memory cache;
- `index.tsx` awaits `hydrateStorage()` before mounting, so the cache is filled
  from `GET /_openhost/session` before anything reads it;
- `setItem`/`removeItem` write through to `PUT /_openhost/session`, serialized so
  a slow request can't land after a newer one.

Logging in through the normal login page is therefore all it takes to persist the
session; logging out clears it server-side. There is no separate settings UI.

The stored access token is a Matrix bearer credential: it can do anything the
admin account can via the admin API, though (unlike a password) it is
individually revocable and can't be replayed against other services. The app is
gated by the OpenHost router (no `public_paths`), so it is not internet-facing.

### fork changes

Everything else in `synapse-admin/` is upstream at tag `0.11.4`.

| file | change |
|---|---|
| `src/storage.ts` | server-backed session store replacing `localStorage` |
| `src/index.tsx` | `hydrateStorage()` before mount; sets the footer version |
| `index.html` | dropped the inline version script (see below) |
| `vite.config.ts` | `define`s `__SYNAPSE_ADMIN_VERSION__` from `package.json` |

The version change fixes an upstream bug: `index.html` referenced
`__SYNAPSE_ADMIN_VERSION__` from a *classic* inline script, which vite's `define`
does not substitute, so it threw in the browser and left the footer blank. Worth
reporting upstream.

## upgrading synapse-admin

```bash
git subtree pull --prefix synapse-admin \
  https://github.com/Awesome-Technologies/synapse-admin.git <tag> --squash
```

Resolve conflicts in the four forked files above, then bump the versions in
`openhost.toml` and `pyproject.toml`. If a release renames the session keys the
authProvider uses, the fork keeps working — `storage.ts` is key-agnostic.

## development

```bash
just setup   # install deps, pre-commit hooks, and the playwright chromium browser
just run     # build the image and serve locally on http://localhost:8080
just test    # run the test suite
just check   # lint, format, typecheck
```

Python here is the app server plus test tooling, managed with
[uv](https://docs.astral.sh/uv/). `just run` persists the session to
`./.local-data`, standing in for the OpenHost app data mount.

`just test` uses the OpenHost test harness (the `openhost[test-harness]` package),
which builds the Dockerfile and runs the app under **podman** (so podman must be
running on the host) fronted by the real OpenHost router. `stack.url` requires
owner auth (use `stack.owner_session` for requests, or `stack.playwright_login(page)`
for browser tests); `stack.app_url` hits the container directly. See `tests/` for the
`stack` fixture.

## remaining work

- The SPA can take ~40s to mount under headless chromium — react-admin stalls
  after its initial checkAuth before mounting. Predates the fork (reproducible
  against upstream's own docker image) and never renders at all under
  playwright's default chromium-headless-shell, hence `--browser-channel
  chromium` in pytest addopts. `test_login_page_renders` is `xfail(strict=False)`
  for this. Root cause not yet found — likely an upstream react-admin 5 /
  react-router 7 race.
- The test harness intermittently fails with "full app did not come up after
  /setup" (a 60s poll of the router's own dashboard, before the app deploys);
  rerunning passes. Needs investigation in the harness, not this repo.
