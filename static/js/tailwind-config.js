// HOODRANKED design tokens
// Kept in its own file so base.html isn't a wall of config.
(function () {
  const config = {
    darkMode: "class",
    theme: {
      extend: {
        colors: {
          outline: "#8e9192",
          "stark-white": "#FFFFFF",
          "pitch-black": "#000000",
          "muted-steel": "#1F2937",
          "surface-gray": "#111111",
          "on-surface-variant": "#c4c7c8",
          blood: "#052F19",
          // blood: "#7A0F0F",
        },
        borderRadius: {
          DEFAULT: "0px",
          lg: "0px",
          xl: "0px",
          full: "9999px",
        },
        spacing: {
          unit: "8px",
          "margin-desktop": "64px",
          "margin-mobile": "20px",
          "container-max": "1440px",
          gutter: "24px",
          "section-gap": "128px",
        },
        fontFamily: {
          display: ["Wallpoet", "sans-serif"],
          displaysec: ["Orbitron", "sans-serif"],
          body: ["Montserrat", "sans-serif"],
          mono: ["JetBrains Mono", "monospace"],
        },
        fontSize: {
          "display-2xl": [
            "120px",
            {
              lineHeight: "110px",
              letterSpacing: "-0.02em",
              fontWeight: "400",
            },
          ],
          "headline-lg": [
            "64px",
            { lineHeight: "64px", letterSpacing: "0.05em", fontWeight: "400" },
          ],
          "headline-lg-mobile": [
            "40px",
            { lineHeight: "40px", fontWeight: "400" },
          ],
          "headline-md": [
            "32px",
            { lineHeight: "36px", letterSpacing: "0.02em", fontWeight: "400" },
          ],
          "body-lg": ["18px", { lineHeight: "28px", fontWeight: "400" }],
          "body-md": ["16px", { lineHeight: "24px", fontWeight: "400" }],
          button: [
            "14px",
            { lineHeight: "14px", letterSpacing: "0.15em", fontWeight: "700" },
          ],
          "label-caps": [
            "12px",
            { lineHeight: "16px", letterSpacing: "0.1em", fontWeight: "500" },
          ],
        },
      },
    },
  };

  const tailwindApi = window.tailwind || {};
  tailwindApi.config = config;
  window.tailwind = tailwindApi;
  globalThis.tailwind = tailwindApi;
})();