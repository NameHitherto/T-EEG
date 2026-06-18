/** @type {import('next').NextConfig} */

// Backend EEG service. The dashboard proxies `/api/<x>` here, wrapping the
// request with the active dataset's segment: `/api/<segment>/<x>`.
// Selection of the segment is driven by the `active_dataset` preference cookie.
const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:13400";

const nextConfig = {
  reactCompiler: true,
  compiler: {
    removeConsole: process.env.NODE_ENV === "production",
  },
  async redirects() {
    return [
      {
        source: "/dashboard",
        destination: "/dashboard/default",
        permanent: false,
      },
    ];
  },
  async rewrites() {
    return [
      // Per-dataset rewrite: `/api/<x>` → `<BACKEND>/api/<segment>/<x>`.
      // Rules are matched top-to-bottom; the first match wins, so cookie-
      // specific rules must come before the default fallback.
      {
        source: "/api/:path*",
        destination: `${BACKEND_URL}/api/seed-v/:path*`,
        has: [{ type: "cookie", key: "active_dataset", value: "seed-v" }],
      },
      // Add more datasets here as `has: cookie` rules before the fallback.
      // Default fallback (first load, no cookie yet) → SEED-V.
      {
        source: "/api/:path*",
        destination: `${BACKEND_URL}/api/seed-v/:path*`,
      },
    ];
  },
};

export default nextConfig;
