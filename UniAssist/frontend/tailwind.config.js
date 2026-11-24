/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        navy: { 50: '#eef2fb', 100: '#d9e2f5', 200: '#b3c4ea', 300: '#7f98d6', 400: '#4d6dbd', 500: '#2a4a9c',
                600: '#1d3a82', 700: '#14306e', 800: '#0f2759', 900: '#0B1F4B', 950: '#071433' },
        brand: { 50: '#f5f3ff', 100: '#ede9fe', 200: '#ddd6fe', 300: '#c4b5fd', 400: '#a78bfa', 500: '#8b5cf6',
                 600: '#7c3aed', 700: '#6d28d9', 800: '#5b21b6', 900: '#4c1d95' },
      },
      fontFamily: { sans: ['Inter', 'system-ui', 'Segoe UI', 'Roboto', 'sans-serif'] },
      keyframes: { fadeUp: { '0%': { opacity: 0, transform: 'translateY(8px)' }, '100%': { opacity: 1, transform: 'none' } } },
      animation: { fadeUp: 'fadeUp .35s ease-out both' },
    },
  },
  plugins: [],
}
