/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: { DEFAULT: '#0b0f14', panel: '#111823', border: '#1e2a38' },
        accent: '#3bd6c6',
      },
      fontFamily: { mono: ['JetBrains Mono', 'ui-monospace', 'monospace'] }
    },
  },
  plugins: [],
}
