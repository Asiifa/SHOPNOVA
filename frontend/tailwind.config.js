/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        navy: "#0B1F3A",
        cream: "#F7F3EE",
        coral: "#E07A5F",
        charcoal: "#1C1917",
        mist: "#6B7280",
        success: "#3F7D5A",
        danger: "#B85C5C",
      },
      fontFamily: {
        sans: ["Manrope", "Inter", "system-ui", "sans-serif"],
      },
      boxShadow: {
        card: "0 1px 2px rgba(28, 25, 23, 0.06), 0 8px 24px rgba(11, 31, 58, 0.06)",
      },
    },
  },
  plugins: [],
};
