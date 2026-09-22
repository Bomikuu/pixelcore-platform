export default defineNuxtConfig({
  ssr: true,
  compatibilityDate: "2026-07-15",
  devtools: { enabled: process.env.NODE_ENV !== "production" },
  routeRules: {
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
    "/site/**": { ssr: true },
  },
  runtimeConfig: {
    apiInternalBaseUrl:
      process.env.NUXT_API_INTERNAL_BASE_URL ||
      process.env.NUXT_PUBLIC_API_BASE_URL ||
      "http://localhost:8000/api/",
    public: {
      apiBaseUrl:
        process.env.NUXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/",
      platformDomain:
        process.env.NUXT_PUBLIC_PLATFORM_DOMAIN || "pixelcore.localhost",
      googleIdentityClientId:
        process.env.NUXT_PUBLIC_GOOGLE_IDENTITY_CLIENT_ID || "",
      mapboxAccessToken:
        process.env.NUXT_PUBLIC_MAPBOX_ACCESS_TOKEN || "",
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
  css: ["~/assets/css/tailwind.css"],
  modules: ["@nuxtjs/tailwindcss", "shadcn-nuxt", "@pinia/nuxt"],
  vite: {
    server: {
      hmr: {
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
