import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { VitePWA } from "vite-plugin-pwa";

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: "autoUpdate",
      includeAssets: ["favicon.ico", "logo_icone.png"],
      manifest: {
        name: "CONEXO - Inteligência Comercial",
        short_name: "CONEXO",
        description: "Pergunte ao seu negócio como se conversasse com alguém.",
        theme_color: "#0f172a",
        background_color: "#0f172a",
        display: "standalone",
        start_url: "/",
        icons: [
          { src: "/logo_icone.png", sizes: "192x192", type: "image/png" },
          { src: "/logo_icone.png", sizes: "512x512", type: "image/png" },
          { src: "/logo_icone.png", sizes: "512x512", type: "image/png", purpose: "maskable" },
        ],
      },
      workbox: {
        // Casca da interface em cache; dados da API sempre frescos da rede
        navigateFallback: "/index.html",
        runtimeCaching: [
          {
            urlPattern: ({ url }) => url.pathname.startsWith("/conexo/"),
            handler: "NetworkOnly",
          },
        ],
      },
    }),
  ],
});
