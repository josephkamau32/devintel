/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      animation: {
        'fade-in': 'fade-in 0.3s ease-out both',
        'slide-up': 'slide-up 0.35s ease-out both',
        'slide-down': 'slide-down 0.35s ease-out both',
        'shimmer': 'shimmer 1.5s infinite',
        'float': 'float 3s ease-in-out infinite',
        'gradient': 'gradient-shift 6s ease infinite',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      backdropBlur: {
        xs: '2px',
      },
      boxShadow: {
        'glow-sm': '0 0 15px rgba(139, 92, 246, 0.15)',
        'glow-md': '0 0 30px rgba(139, 92, 246, 0.2)',
        'glow-lg': '0 0 50px rgba(139, 92, 246, 0.25)',
      },
    },
  },
  plugins: [],
};
