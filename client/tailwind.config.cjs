/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        "xrpl-blue": "#0040ff",
        "xrpl-green": "#00e09d",
      },
    },
  },
  plugins: [],
};
