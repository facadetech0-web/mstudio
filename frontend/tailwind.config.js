/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        studio: {
          950: '#07090e',
          900: '#0c0f17',
          850: '#111520',
          800: '#171d2c',
          700: '#222b40',
          600: '#323d57',
          500: '#4a5778',
          gold: '#f59e0b',
          amber: '#d97706',
          cinema: '#e11d48',
          accent: '#3b82f6',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      }
    },
  },
  plugins: [],
}
