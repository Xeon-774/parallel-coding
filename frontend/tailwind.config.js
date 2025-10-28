/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'worker': '#3b82f6',
        'orchestrator': '#8b5cf6',
      }
    },
  },
  plugins: [],
}
