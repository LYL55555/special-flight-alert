export default async function handler(req, res) {
  const airport = String(req.query.airport || "").trim().toUpperCase();

  if (!airport) {
    return res.status(400).json({ detail: "airport is required" });
  }

  const bases = [
    process.env.TUNNEL_API_BASE_URL,
    process.env.RENDER_API_BASE_URL || "https://special-flight-alert.onrender.com",
  ].filter(Boolean);

  let lastError = null;

  for (const base of bases) {
    try {
      const url = `${base.replace(/\/$/, "")}/api/scan?airport=${encodeURIComponent(airport)}`;

      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 20000);

      const upstream = await fetch(url, {
        method: "GET",
        signal: controller.signal,
        headers: {
          Accept: "application/json",
          "X-Proxy-Source": "vercel",
        },
      });

      clearTimeout(timeout);

      let data;
      try {
        data = await upstream.json();
      } catch (e) {
        throw new Error("Invalid JSON from upstream");
      }

      if (!upstream.ok) {
        if (upstream.status >= 500 || upstream.status === 429) {
          throw new Error(data?.detail || data?.message || `HTTP ${upstream.status}`);
        }
        return res.status(upstream.status).json(data);
      }

      return res.status(200).json({
        ...data,
        proxiedBy: "vercel",
        upstreamBase: base.includes("onrender.com") ? "render" : "tunnel",
      });
    } catch (e) {
      lastError = e;
      console.warn("Upstream failed:", base, e.message);
    }
  }

  return res.status(503).json({
    airport,
    status: "degraded",
    source: "vercel-proxy",
    message: "Live flight data is temporarily unavailable. Please try again later.",
    flights: [],
    error: lastError ? lastError.message : "All upstream APIs failed",
  });
}
