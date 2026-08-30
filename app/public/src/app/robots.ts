import type { MetadataRoute } from "next";

import { PUBLIC_SITE_ORIGIN } from "@/lib/public-seo";

export default function robots(): MetadataRoute.Robots {
  if (process.env.VERCEL_ENV && process.env.VERCEL_ENV !== "production") {
    return {
      rules: {
        userAgent: "*",
        disallow: "/"
      }
    };
  }

  return {
    rules: {
      userAgent: "*",
      allow: "/",
      disallow: ["/api/", "/admin"]
    },
    sitemap: PUBLIC_SITE_ORIGIN + "/sitemap.xml",
    host: PUBLIC_SITE_ORIGIN
  };
}
