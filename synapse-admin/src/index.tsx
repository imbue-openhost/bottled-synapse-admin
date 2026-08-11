import React from "react";

import { createRoot } from "react-dom/client";

import App from "./App";
import { AppContext } from "./AppContext";
import { hydrateStorage } from "./storage";

// Substituted by vite's `define` (see vite.config.ts).
declare const __SYNAPSE_ADMIN_VERSION__: string;

const versionSpan = document.getElementById("version");
if (versionSpan) versionSpan.textContent = __SYNAPSE_ADMIN_VERSION__;

const baseUrl = import.meta.env.BASE_URL;
const configJSON = "config.json";
// if import.meta.env.BASE_URL have a trailing slash, remove it
// load config.json from relative path if import.meta.env.BASE_URL is None or empty
const configJSONUrl = baseUrl ? `${baseUrl.replace(/\/$/, "")}/${configJSON}` : configJSON;

// OpenHost fork: the session lives on the server, so it must be loaded before anything reads storage.
Promise.all([fetch(configJSONUrl).then(res => res.json()), hydrateStorage()]).then(([props]) =>
  createRoot(document.getElementById("root")).render(
    <React.StrictMode>
      <AppContext.Provider value={props}>
        <App />
      </AppContext.Provider>
    </React.StrictMode>
  )
);
