/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      /* ─── Color System ─── */
      colors: {
        brand: {
          50: '#eef2ff',
          100: '#e0e7ff',
          200: '#c7d2fe',
          300: '#a5b4fc',
          400: '#818cf8',
          500: '#6366f1',
          600: '#4f46e5',
          700: '#4338ca',
          800: '#3730a3',
          900: '#312e81',
          950: '#1e1b4b',
        },
        surface: {
          0: '#09090b',    /* App background */
          1: '#0c0c0f',    /* Raised surface */
          2: '#111114',    /* Card background */
          3: '#16161a',    /* Input/field background */
          4: '#1c1c21',    /* Hover state */
          5: '#232329',    /* Active/pressed */
        },
        border: {
          DEFAULT: 'rgba(255, 255, 255, 0.06)',
          subtle: 'rgba(255, 255, 255, 0.04)',
          medium: 'rgba(255, 255, 255, 0.08)',
          strong: 'rgba(255, 255, 255, 0.12)',
          focus: '#6366f1',
        },
        text: {
          primary: '#fafafa',
          secondary: '#a1a1aa',
          tertiary: '#71717a',
          quaternary: '#52525b',
          inverse: '#09090b',
        },
        status: {
          success: '#22c55e',
          'success-muted': 'rgba(34, 197, 94, 0.12)',
          warning: '#f59e0b',
          'warning-muted': 'rgba(245, 158, 11, 0.12)',
          error: '#ef4444',
          'error-muted': 'rgba(239, 68, 68, 0.12)',
          info: '#3b82f6',
          'info-muted': 'rgba(59, 130, 246, 0.12)',
        },
        /* Score tier colors */
        score: {
          critical: '#ef4444',
          'critical-muted': 'rgba(239, 68, 68, 0.12)',
          warning: '#f59e0b',
          'warning-muted': 'rgba(245, 158, 11, 0.12)',
          good: '#22c55e',
          'good-muted': 'rgba(34, 197, 94, 0.12)',
          excellent: '#06b6d4',
          'excellent-muted': 'rgba(6, 182, 212, 0.12)',
          neutral: '#71717a',
          'neutral-muted': 'rgba(113, 113, 122, 0.12)',
        },
      },

      /* ─── Spacing tokens ─── */
      spacing: {
        'sidebar': '240px',
        'sidebar-collapsed': '64px',
        'topbar': '56px',
      },

      /* ─── Typography ─── */
      fontSize: {
        'display': ['3.5rem', { lineHeight: '1.1', letterSpacing: '-0.025em', fontWeight: '700' }],
        'h1': ['2.25rem', { lineHeight: '1.2', letterSpacing: '-0.02em', fontWeight: '700' }],
        'h2': ['1.75rem', { lineHeight: '1.25', letterSpacing: '-0.015em', fontWeight: '600' }],
        'h3': ['1.25rem', { lineHeight: '1.35', letterSpacing: '-0.01em', fontWeight: '600' }],
        'h4': ['1.075rem', { lineHeight: '1.4', letterSpacing: '-0.005em', fontWeight: '600' }],
        'body': ['0.875rem', { lineHeight: '1.6', fontWeight: '400' }],
        'body-sm': ['0.8125rem', { lineHeight: '1.55', fontWeight: '400' }],
        'caption': ['0.75rem', { lineHeight: '1.5', fontWeight: '500' }],
        'overline': ['0.6875rem', { lineHeight: '1.4', letterSpacing: '0.05em', fontWeight: '500' }],
        'stat': ['2rem', { lineHeight: '1.1', letterSpacing: '-0.02em', fontWeight: '700' }],
        'stat-sm': ['1.5rem', { lineHeight: '1.1', letterSpacing: '-0.02em', fontWeight: '700' }],
      },

      /* ─── Border Radius ─── */
      borderRadius: {
        'xs': '4px',
        'sm': '6px',
        'md': '8px',
        'lg': '10px',
        'xl': '12px',
        '2xl': '16px',
      },

      /* ─── Shadows / Elevation ─── */
      boxShadow: {
        'subtle': '0 1px 2px rgba(0, 0, 0, 0.3), 0 1px 3px rgba(0, 0, 0, 0.15)',
        'medium': '0 4px 12px rgba(0, 0, 0, 0.35), 0 2px 4px rgba(0, 0, 0, 0.2)',
        'elevated': '0 8px 30px rgba(0, 0, 0, 0.4), 0 4px 8px rgba(0, 0, 0, 0.25)',
        'overlay': '0 16px 48px rgba(0, 0, 0, 0.5), 0 8px 16px rgba(0, 0, 0, 0.3)',
        'focus-ring': '0 0 0 3px rgba(99, 102, 241, 0.25)',
        'focus-ring-error': '0 0 0 3px rgba(239, 68, 68, 0.25)',
        'glow-brand': '0 0 20px rgba(99, 102, 241, 0.15)',
        'glow-success': '0 0 20px rgba(34, 197, 94, 0.15)',
      },

      /* ─── Animations ─── */
      animation: {
        'fade-in': 'di-fade-in 0.25s ease-out both',
        'fade-out': 'di-fade-out 0.2s ease-in both',
        'slide-up': 'di-slide-up 0.3s ease-out both',
        'slide-down': 'di-slide-down 0.3s ease-out both',
        'slide-in-left': 'di-slide-in-left 0.3s ease-out both',
        'scale-in': 'di-scale-in 0.2s ease-out both',
        'shimmer': 'di-shimmer 1.8s linear infinite',
        'spin-slow': 'spin 1.2s linear infinite',
        'pulse-subtle': 'di-pulse-subtle 2.5s ease-in-out infinite',
        'score-fill': 'di-score-fill 1s ease-out both',
        'count-up': 'di-fade-in 0.4s ease-out both',
        'width-expand': 'di-width-expand 0.8s ease-out both',
      },
      keyframes: {
        'di-fade-in': {
          from: { opacity: '0' },
          to: { opacity: '1' },
        },
        'di-fade-out': {
          from: { opacity: '1' },
          to: { opacity: '0' },
        },
        'di-slide-up': {
          from: { opacity: '0', transform: 'translateY(8px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
        'di-slide-down': {
          from: { opacity: '0', transform: 'translateY(-8px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
        'di-slide-in-left': {
          from: { opacity: '0', transform: 'translateX(-8px)' },
          to: { opacity: '1', transform: 'translateX(0)' },
        },
        'di-scale-in': {
          from: { opacity: '0', transform: 'scale(0.97)' },
          to: { opacity: '1', transform: 'scale(1)' },
        },
        'di-shimmer': {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
        'di-pulse-subtle': {
          '0%, 100%': { opacity: '0.5' },
          '50%': { opacity: '1' },
        },
        'di-score-fill': {
          from: { strokeDashoffset: '283' },
          to: { strokeDashoffset: 'var(--score-offset)' },
        },
        'di-width-expand': {
          from: { width: '0%' },
          to: { width: 'var(--bar-width)' },
        },
      },

      /* ─── Transitions ─── */
      transitionDuration: {
        '150': '150ms',
        '200': '200ms',
      },

      /* ─── Backdrop Blur ─── */
      backdropBlur: {
        xs: '2px',
      },
    },
  },
  plugins: [],
};
