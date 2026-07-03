import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
// The FastAPI backend runs on :8000 and already allows CORS from any origin,
// so a direct fetch works. We also proxy /brief in dev so the frontend can use
// a relative URL and not care about the host.
export default defineConfig({
    plugins: [react()],
    server: {
        port: 5173,
        proxy: {
            "/api": {
                target: "http://127.0.0.1:8000",
                changeOrigin: true,
                rewrite: function (path) { return path.replace(/^\/api/, ""); },
            },
        },
    },
});
