import { readFileSync } from "node:fs";

import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// index.html references __SYNAPSE_ADMIN_VERSION__ but upstream never defines it, so the released
// index.html throws in the browser. Substitute it from package.json at build time.
const { version } = JSON.parse(readFileSync(new URL("./package.json", import.meta.url), "utf-8"));

export default defineConfig(({ mode }) => ({
  plugins: [
    react(),
  ],
  define: {
    __SYNAPSE_ADMIN_VERSION__: JSON.stringify(version),
  },
  server: {
    host: true,
  },
  base: './',
  build: {
    chunkSizeWarningLimit: 1500,
    sourcemap: mode === 'development',
  },
  test: {
    globals: true,
    environment: 'happy-dom',
    setupFiles: "./src/vitest.setup.ts",
  },
  ssr: {
    noExternal: ['react-dropzone', 'react-admin', 'ra-ui-materialui'],
  },
}));
