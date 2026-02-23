/** @type {import('tailwindcss').Config} */
export default {
  content: ["./src/**/*.{astro,html,js,jsx,ts,tsx,md,mdx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui"],
        mono: ["JetBrains Mono", "ui-monospace", "SFMono-Regular"]
      },
      colors: {
        primary: {
          900: "#0F2D4A",
          700: "#1A4F7A",
          500: "#2574B0",
          100: "#E8F2FB"
        }
      },
      boxShadow: {
        "nav": "0 1px 0 #e5e7eb"
      }
    }
  },
  plugins: []
};
