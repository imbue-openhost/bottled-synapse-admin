// OpenHost fork: session state (access token, homeserver, ...) is kept on the server instead of in
// localStorage, so every browser reaching this app shares one login. Call sites read storage during
// render, so the Storage-shaped API stays synchronous: reads are served from a cache that
// hydrateStorage() fills before the app mounts, and writes are pushed to the server in the background.

const baseUrl = import.meta.env.BASE_URL;
const sessionPath = "_openhost/session";
const sessionUrl = baseUrl ? `${baseUrl.replace(/\/$/, "")}/${sessionPath}` : sessionPath;

let cache: Record<string, string> = {};
let writes: Promise<unknown> = Promise.resolve();

// Serialize writes: a slow request must not land after a newer one and resurrect stale state.
function persist(): void {
  const snapshot = { ...cache };
  writes = writes.then(() =>
    fetch(sessionUrl, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(snapshot),
      // logout removes the token and then navigates; keepalive lets the write outlive the page.
      keepalive: true,
    }).catch(error => console.error("could not persist session to the server", error))
  );
}

export async function hydrateStorage(): Promise<void> {
  try {
    const response = await fetch(sessionUrl);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    cache = await response.json();
  } catch (error) {
    // Render anyway with an empty session: the user gets the login page rather than a stuck spinner.
    console.error("could not load the stored session; starting logged out", error);
    cache = {};
  }
}

const storage = {
  getItem(key: string): string | null {
    return Object.prototype.hasOwnProperty.call(cache, key) ? cache[key] : null;
  },
  setItem(key: string, value: string): void {
    cache[key] = String(value);
    persist();
  },
  removeItem(key: string): void {
    delete cache[key];
    persist();
  },
  clear(): void {
    cache = {};
    persist();
  },
};

export default storage;
