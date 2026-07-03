/** @type {import('tailwindcss').Config} */
// Design tokens lifted from the EMIAC Intelligence Stitch design system
// (DESIGN.md): "Strategic Precision" — Forest Green brand, warm paper
// backgrounds, Plus Jakarta Sans + DM Sans, tonal-layer depth over shadows.
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        primary: "#004931",
        "primary-container": "#006344",
        "brand-deep": "#004D35",
        "primary-fixed": "#a2f3cb",
        "primary-fixed-dim": "#86d7b0",
        "on-primary-container": "#8cdcb5",
        "surface-tint": "#126b4c",
        secondary: "#5e5e5c",
        "surface-paper": "#F6F4F1",
        "surface-bright": "#f9f9f9",
        surface: "#f9f9f9",
        "surface-container-low": "#f3f3f3",
        "surface-container": "#eeeeee",
        "surface-container-high": "#e8e8e8",
        "surface-container-highest": "#e2e2e2",
        "surface-variant": "#e2e2e2",
        "on-surface": "#1b1b1b",
        "on-surface-variant": "#3f4943",
        outline: "#6f7a72",
        "outline-variant": "#bec9c1",
        error: "#ba1a1a",
        "error-container": "#ffdad6",
        "on-error-container": "#93000a",
        amber: "#b8860b",
        white: "#FFFFFF",
      },
      fontFamily: {
        display: ["Plus Jakarta Sans", "sans-serif"],
        heading: ["Plus Jakarta Sans", "sans-serif"],
        body: ["DM Sans", "sans-serif"],
      },
      borderRadius: {
        DEFAULT: "0.25rem",
        lg: "0.5rem",
        xl: "0.75rem",
      },
      spacing: {
        gutter: "24px",
        "margin-desktop": "40px",
        "section-gap": "80px",
      },
      maxWidth: {
        container: "1440px",
      },
      boxShadow: {
        module: "0 2px 12px rgba(0,77,53,0.04)",
        modal: "0 12px 40px rgba(0,77,53,0.12)",
      },
      keyframes: {
        "fade-up": {
          "0%": { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
      },
      animation: {
        "fade-up": "fade-up 0.4s ease-out forwards",
      },
    },
  },
  plugins: [],
};
