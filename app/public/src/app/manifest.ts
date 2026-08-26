import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "SwitchaBank",
    short_name: "SwitchaBank",
    description:
      "Compare reviewed deposit, credit card, and loan facts across banks.",
    start_url: "/",
    display: "standalone",
    background_color: "#f6f1e8",
    theme_color: "#0d4f3c",
    icons: [{
      src: "/icon.svg",
      sizes: "any",
      type: "image/svg+xml"
    }]
  };
}
