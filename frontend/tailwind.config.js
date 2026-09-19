/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        canvas: '#F7F8F6',
        white: '#FFFFFF',
        ink: '#18201D',
        'muted-ink': '#66706B',
        silver: '#D7DDD9',
        'deep-silver': '#AAB3AE',
        cyan: '#32C7C3',
        emerald: '#35A56B',
        gold: '#C7A45A',
        'pale-gold': '#E9D9AF',
      },
      fontFamily: {
        heading: ['"Space Grotesk"', 'sans-serif'],
        sans: ['Inter', 'sans-serif'],
        mono: ['"IBM Plex Mono"', 'monospace'],
      },
      backdropBlur: {
        glass: '20px',
      },
      boxShadow: {
        glass: '0 2px 16px rgba(0,0,0,0.04)',
        'glass-lg': '0 4px 24px rgba(0,0,0,0.06)',
        card: '0 1px 4px rgba(0,0,0,0.03)',
      },
    },
  },
  plugins: [],
}
