window.SPECIAL_FLIGHT_CONFIG = {
  // Vercel / public frontend: optional home tunnel (free). Run ./scripts/run_tunnel.sh
  // and paste the https://....trycloudflare.com URL here. Leave "" if not running.
  tunnelApiBaseUrl: "https://occupied-mills-dinner-pennsylvania.trycloudflare.com",

  // Always-on fallback (Render). May return degraded when FR24 blocks datacenter IP.
  apiBaseUrl: "https://special-flight-alert.onrender.com",
};
