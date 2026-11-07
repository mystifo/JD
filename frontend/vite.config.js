import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: process.env.VITE_DEV_API_TARGET || "http://localhost:8000",
        changeOrigin: false,
      },
    },
  },
  build: {
    sourcemap: true,
    chunkSizeWarningLimit: 700,
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: "./src/test/setup.js",
    css: true,
    restoreMocks: true,
    clearMocks: true,
  },
});
