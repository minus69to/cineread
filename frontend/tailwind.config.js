/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{html,js,svelte,ts}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        'cine-bg': '#0f0f13',
        'cine-card': '#1a1a24',
        'cine-border': '#2a2a3a',
        'cine-accent': '#7c6af7',
        'cine-accent-hover': '#6a58e0',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      animation: {
        'pulse-soft': 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      }
    }
  },
  plugins: []
};
