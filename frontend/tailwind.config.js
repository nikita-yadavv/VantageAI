/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        palette: {
          lightest: '#FAF6FA', // Soft warm pearlescent base
          lilac: '#EAE2ED',    // Lilac
          heather: '#D7C9DB',  // Heather Lavender
          mauve: '#BAA7BF',    // Mauve Orchid
          plum: '#6E5C73',     // Darkened Plum for crisp readability
          deep: '#2F2433',     // High-contrast Deep Aubergine for sharp headings & text
        }
      },
      fontFamily: {
        sans: ['Inter', '"Plus Jakarta Sans"', 'system-ui', 'sans-serif'],
        display: ['"Plus Jakarta Sans"', 'Inter', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
      boxShadow: {
        'glass': '0 20px 45px -12px rgba(81, 67, 84, 0.12), inset 0 1px 1px 0 rgba(255, 255, 255, 0.95)',
        'glass-hover': '0 25px 50px -12px rgba(81, 67, 84, 0.18), inset 0 1px 1px 0 rgba(255, 255, 255, 1)',
      }
    },
  },
  plugins: [],
}
