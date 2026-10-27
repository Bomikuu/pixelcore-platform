import { fileURLToPath } from "node:url";
export default defineNuxtConfig({
  ssr: true,
  compatibilityDate: "2026-07-15",
  devtools: { enabled: process.env.NODE_ENV !== "production" },
  routeRules: {
    "/studio-connect": { ssr: false },
    "/workspace/**": { ssr: false },
    "/settings/**": { ssr: false },
    "/login": { ssr: false },
    "/register": { ssr: false },
    "/verify-email": { ssr: false },
    "/forgot-password": { ssr: false },
    "/reset-password": { ssr: false },
    "/onboarding": { ssr: false },
    "/accept-invitation": { ssr: false },
    "/employee-onboarding": { ssr: false },
    "/employee": { ssr: false },
    "/rider/**": { ssr: false },
    "/site/**": { ssr: true },
  },
  runtimeConfig: {
    smokeyAssetProxyOrigin:
      process.env.NUXT_SMOKEY_ASSET_PROXY_ORIGIN || "http://127.0.0.1",
    apiInternalBaseUrl:
      process.env.NUXT_API_INTERNAL_BASE_URL ||
      process.env.NUXT_PUBLIC_API_BASE_URL ||
      "http://localhost:8000/api/",
    public: {
      smokeyUiMode:
        process.env.NUXT_PUBLIC_SMOKEY_UI_MODE ||
        (process.env.NODE_ENV === "production" ? "legacy" : "module"),
      smokeyUiSource:
        process.env.NUXT_PUBLIC_SMOKEY_UI_SOURCE ||
        (process.env.NODE_ENV === "production" ? "release" : "development"),
      smokeyUiManifest:
        process.env.NUXT_PUBLIC_SMOKEY_UI_MANIFEST ||
        "/smokey-assets/channels/stable-v1.json",
      studioOrigin:
        process.env.NUXT_PUBLIC_STUDIO_ORIGIN || "http://localhost:4173",
      apiBaseUrl:
        process.env.NUXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/",
      platformDomain:
        process.env.NUXT_PUBLIC_PLATFORM_DOMAIN || "pixelcore.localhost",
      googleIdentityClientId:
        process.env.NUXT_PUBLIC_GOOGLE_IDENTITY_CLIENT_ID || "",
      mapboxAccessToken: process.env.NUXT_PUBLIC_MAPBOX_ACCESS_TOKEN || "",
    },
  },
  app: {
    head: {
      title: "PixelCore",
      meta: [
        {
          name: "description",
          content: "A configurable operating core for modern businesses.",
        },
        { name: "viewport", content: "width=device-width, initial-scale=1" },
        { name: "theme-color", content: "#102A2A" },
      ],
      link: [
        { rel: "icon", href: "/pixelcore-mark.svg" },
        {
          rel: "stylesheet",
          href: "https://fonts.googleapis.com/css2?family=Alex+Brush&family=Allura&family=Cormorant+Garamond:wght@500;600;700&family=Great+Vibes&family=Inter:wght@400;500;600;700;800&family=Lobster&family=Manrope:wght@400;500;600;700;800&family=Montserrat:wght@400;500;600;700;800&family=Newsreader:opsz,wght@6..72,500;6..72,600;6..72,700&family=Parisienne&family=Playball&family=Playfair+Display:wght@600;700;800&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Poppins:wght@400;500;600;700;800&display=swap",
        },
      ],
    },
  },
  css: ["~/assets/css/tailwind.css", "@sitebuilder/renderer/fonts.css"],
  modules: ["@nuxtjs/tailwindcss", "shadcn-nuxt", "@pinia/nuxt"],
  colorMode: {
    preference: "system",
    fallback: "light",
    classSuffix: "",
    storage: "localStorage",
    storageKey: "pixelcore-workspace-theme",
  },
  vite: {
    resolve: { dedupe: ["vue"] },
    server: {
      fs: {
        allow: [
          fileURLToPath(new URL("./", import.meta.url)),
          fileURLToPath(new URL("../../website-builder/", import.meta.url)),
        ],
      },
      hmr:
        process.env.PIXELCORE_LOCAL_DEV === "1"
          ? undefined
          : {
              clientPort: 80,
              protocol: "ws",
            },
    },
  },
  shadcn: {
    prefix: "",
    componentDir: "./components/ui",
  },
});
