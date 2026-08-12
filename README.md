# bottled-synapse-admin

[synapse-admin](https://github.com/Awesome-Technologies/synapse-admin) packaged
as an [Cloud in a Bottle](https://github.com/imbue-openhost/Cloud in a Bottle) app: an admin UI
for [Matrix Synapse](https://github.com/element-hq/synapse) homeservers (manage
users, rooms, media, reports, ...).

Upstream lives in `synapse-admin/` as a **git subtree**, lightly forked and built
from source. A small Python (Litestar) server serves the build and owns the one
piece of state that isn't upstream's: the Matrix session.

## the fork: the session lives on the server

Stock synapse-admin keeps the session (homeserver URL, access token, user id,
device id) in the browser's `localStorage`, so every browser needs its own login.
Here it lives on the Cloud in a Bottle instance instead, at
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
gated by the Cloud in a Bottle router (no `public_paths`), so it is not internet-facing.

## the fork: federated users have no user page

Synapse's admin API only knows users **local** to the homeserver you are logged
into; asking it about anyone else gives `400 M_UNKNOWN "Can only look up local
users"`. Upstream ignores this and renders every Matrix ID as a link to
`/users/<id>`, so in a federated room most of those links open a page whose
`getOne` fails, and react-admin bounces straight back to the user list.

`src/openhost/` renders remote IDs as plain text tagged with their origin server
instead, and drops the link. It also adds the one administrative action a
homeserver *can* take on a user it doesn't own: kicking them out of a room, via
`POST /_matrix/client/v3/rooms/{roomId}/kick`, per row or over a selection. This
needs a power level of at least the room's `kick` level (50 by default).

Note that a homeserver whose rooms are all federated legitimately shows a
near-empty user list — that is the admin API working correctly, not a bug.

### fork changes

Everything else in `synapse-admin/` is upstream at tag `0.11.4`.

| file | change |
|---|---|
| `src/storage.ts` | server-backed session store replacing `localStorage` |
| `src/index.tsx` | `hydrateStorage()` before mount; sets the footer version |
| `index.html` | dropped the inline version script (see below) |
| `vite.config.ts` | `define`s `__SYNAPSE_ADMIN_VERSION__` from `package.json` |
| `src/openhost/` | new; the federation-aware member list and user links |
| `src/resources/rooms.tsx` | members tab, room `creator` and state-event `sender` come from `src/openhost/` |
| `src/synapse/dataProvider.ts` | `jsonClient` exported so `src/openhost/` can reach non-resource endpoints |

New behaviour lives in `src/openhost/` so the diff against upstream files stays
to an import and a tag; conflicts on a subtree pull should be trivial.

The version change fixes an upstream bug: `index.html` referenced
`__SYNAPSE_ADMIN_VERSION__` from a *classic* inline script, which vite's `define`
does not substitute, so it threw in the browser and left the footer blank. Worth
reporting upstream — as is the dead link, which is not Cloud in a Bottle-specific.

## upgrading synapse-admin

```bash
git subtree pull --prefix synapse-admin \
  https://github.com/Awesome-Technologies/synapse-admin.git <tag> --squash
```

Resolve conflicts in the forked files above, then bump the versions in
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
`./.local-data`, standing in for the Cloud in a Bottle app data mount.

`just test` uses the Cloud in a Bottle test harness (the `openhost[test-harness]` package),
which builds the Dockerfile and runs the app under **podman** (so podman must be
running on the host) fronted by the real Cloud in a Bottle router. `stack.url` requires
owner auth (use `stack.owner_session` for requests, or `stack.playwright_login(page)`
for browser tests); `stack.app_url` hits the container directly. See `tests/` for the
`stack` fixture.

## remaining work

- Playwright's locator waits (`expect(...).to_be_visible`) stall against this app,
  so `test_login_page_renders` is `xfail(strict=False)` on a 30s budget. The app
  itself renders in about a second — the container log shows the login page's
  background `floating-cogs.svg` fetched right after the bundle. Chromium launches
  in 0.3s, a CPU profile of the stall is ~100% idle, and upstream's own image
  behaves the same, so this is a Playwright interaction rather than an app defect.
  The non-browser tests cover the fork's wiring instead.

  If you write probes for this, two traps: `wait_until="commit"` returns before an
  execution context exists, so a following `page.evaluate` blocks forever; and
  `time.sleep()` does not pump sync Playwright's event loop, so queued events never
  dispatch and a healthy page looks dead. Use the default `wait_until` and
  `page.wait_for_timeout()`.
- The SPA does not render under playwright's default chromium-headless-shell,
  hence `--browser-channel chromium` in pytest addopts.
- The test harness intermittently fails with "full app did not come up after
  /setup" (a 60s poll of the router's own dashboard, before the app deploys);
  rerunning passes. Needs investigation in the harness, not this repo.
