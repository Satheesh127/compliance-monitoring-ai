/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      fontFamily: {
        heading: ["Space Grotesk", "sans-serif"],
        body: ["IBM Plex Sans", "sans-serif"],
      },
      colors: {
        surface: "#f5f7fb",
        ink: "#0f172a",
        danger: "#dc2626",
        warning: "#ca8a04",
        safe: "#16a34a",
      },
      boxShadow: {
        soft: "0 10px 30px rgba(15, 23, 42, 0.08)",
      },
      keyframes: {
        rise: {
          "0%": { opacity: 0, transform: "translateY(18px)" },
          "100%": { opacity: 1, transform: "translateY(0)" },
        },
      },
      animation: {
        rise: "rise 0.45s ease-out forwards",
      },
    },
  },
  plugins: [],
};
