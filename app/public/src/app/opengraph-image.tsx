import { ImageResponse } from "next/og";

export const alt = "SwitchaBank — compare banks and financial products";
export const size = {
  width: 1200,
  height: 630
};
export const contentType = "image/png";

export default function OpenGraphImage() {
  return new ImageResponse(
    (
      <div
        style={{
          alignItems: "stretch",
          background: "#f6f1e8",
          color: "#17201d",
          display: "flex",
          flexDirection: "column",
          fontFamily: "Arial, sans-serif",
          height: "100%",
          justifyContent: "space-between",
          padding: "72px 80px",
          width: "100%"
        }}
      >
        <div
          style={{
            alignItems: "center",
            display: "flex",
            fontSize: 38,
            fontWeight: 700,
            gap: 18,
            letterSpacing: "-1.5px"
          }}
        >
          <div
            style={{
              alignItems: "center",
              background: "#0d4f3c",
              borderRadius: 22,
              color: "#ffffff",
              display: "flex",
              flexDirection: "column",
              gap: 9,
              height: 78,
              justifyContent: "center",
              width: 78
            }}
          >
            <div style={{ alignItems: "center", display: "flex" }}>
              <div style={{ background: "#ffffff", height: 5, width: 35 }} />
              <div
                style={{
                  borderBottom: "7px solid transparent",
                  borderLeft: "10px solid #ffffff",
                  borderTop: "7px solid transparent",
                  display: "flex",
                  height: 0,
                  width: 0
                }}
              />
            </div>
            <div style={{ alignItems: "center", display: "flex" }}>
              <div
                style={{
                  borderBottom: "7px solid transparent",
                  borderRight: "10px solid #ffffff",
                  borderTop: "7px solid transparent",
                  display: "flex",
                  height: 0,
                  width: 0
                }}
              />
              <div style={{ background: "#ffffff", height: 5, width: 35 }} />
            </div>
          </div>
          SwitchaBank
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: 26 }}>
          <div
            style={{
              display: "flex",
              fontSize: 76,
              fontWeight: 700,
              letterSpacing: "-4px",
              lineHeight: 1.02,
              maxWidth: 980
            }}
          >
            Compare banks. Compare products. Switch smarter.
          </div>
          <div
            style={{
              color: "#53615c",
              display: "flex",
              fontSize: 28
            }}
          >
            Reviewed deposits · credit cards · loans
          </div>
        </div>
        <div
          style={{
            borderTop: "2px solid #d6cfc3",
            color: "#0d4f3c",
            display: "flex",
            fontSize: 22,
            paddingTop: 22
          }}
        >
          switchabank.com
        </div>
      </div>
    ),
    size
  );
}
