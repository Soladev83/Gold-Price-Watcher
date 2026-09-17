import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      // In development, proxy /api calls to the local FastAPI backend
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
  define: {
    // Make the backend URL available at build time for production deployments.
    // In dev the proxy above handles /api, so this only matters after `npm run build`.
    __API_BASE_URL__: JSON.stringify(process.env.VITE_API_BASE_URL ?? ""),
  },
});
