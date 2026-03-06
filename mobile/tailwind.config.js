/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./app/**/*.{ts,tsx}', './components/**/*.{ts,tsx}'],
  presets: [require('nativewind/preset')],
  theme: {
    extend: {
      colors: {
        primary: '#7c3aed',
        background: '#0f0a2e',
        surface: 'rgba(255,255,255,0.05)',
        'surface-strong': 'rgba(255,255,255,0.08)',
        border: 'rgba(255,255,255,0.08)',
      },
    },
  },
  plugins: [],
};
