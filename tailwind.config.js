/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        hhgoa: {
          bg: "#FAFAFA",
          card: "#FFFFFF",
          text: "#111111",
          muted: "#666666",
          border: "#E5E5E5",
          highlight: "#F3F4F6",
          orange: "#FF6B00",
          black: "#111111",
        },
      },
      fontFamily: {
        hhgoa: ["var(--font-hhgoa)", "Outfit", "Inter", "sans-serif"],
      },
      borderRadius: {
        "2xl": "1rem",
        "3xl": "1.5rem",
        "4xl": "2rem",
      },
      boxShadow: {
        subtle: "0 1px 3px 0 rgba(0, 0, 0, 0.05), 0 1px 2px 0 rgba(0, 0, 0, 0.03)",
        card: "0 4px 20px -2px rgba(0, 0, 0, 0.04)",
        float: "0 10px 30px -5px rgba(0, 0, 0, 0.08)",
      },
    },
  },
  plugins: [],
};
