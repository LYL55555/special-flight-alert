// Production API order: Cloudflare Named Tunnel (primary) → Render (fallback).
// Replace YOUR_DOMAIN.com with your real domain before going live.
window.APP_CONFIG = {
  apiBaseUrls: [
    "https://flight-api.YOUR_DOMAIN.com",
    "https://special-flight-alert.onrender.com",
  ],
};
