/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        ink: '#070b14',
        panel: '#0c1322',
        line: '#1d2a3d',
        cyan: '#2dd4bf',
      },
      fontFamily: {
        sans: ['Inter', 'Segoe UI', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        display: ['Segoe UI', 'Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        panel: '0 24px 70px -32px rgba(0, 0, 0, 0.72)',
      },
    },
  },
  plugins: [],
}
