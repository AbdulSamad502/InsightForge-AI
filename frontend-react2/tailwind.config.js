/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        bg: {
          primary:   '#07070f',
          secondary: '#0d0d1a',
          card:      '#12121f',
          hover:     '#16162a',
          border:    '#1e1e35',
        },
        accent: {
          primary:   '#6366f1',
          secondary: '#8b5cf6',
          success:   '#10b981',
          warning:   '#f59e0b',
          danger:    '#ef4444',
          cyan:      '#06b6d4',
        },
        text: {
          primary:   '#f1f5f9',
          secondary: '#94a3b8',
          muted:     '#475569',
        }
      },
      fontFamily: {
        sans:  ['Inter', 'system-ui', 'sans-serif'],
        mono:  ['JetBrains Mono', 'monospace'],
        display: ['Cal Sans', 'Inter', 'sans-serif'],
      },
      backgroundImage: {
        'gradient-primary':  'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
        'gradient-card':     'linear-gradient(145deg, #12121f 0%, #0d0d1a 100%)',
        'gradient-glow':     'radial-gradient(circle at 50% 0%, rgba(99,102,241,0.15) 0%, transparent 60%)',
      },
      boxShadow: {
        'glow':       '0 0 30px rgba(99,102,241,0.2)',
        'glow-sm':    '0 0 15px rgba(99,102,241,0.15)',
        'glow-green': '0 0 20px rgba(16,185,129,0.2)',
        'card':       '0 4px 24px rgba(0,0,0,0.4)',
      },
      animation: {
        'pulse-slow':    'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'fade-in':       'fadeIn 0.3s ease-in-out',
        'slide-up':      'slideUp 0.3s ease-out',
        'shimmer':       'shimmer 2s infinite',
      },
      keyframes: {
        fadeIn:  { from: { opacity: 0 }, to: { opacity: 1 } },
        slideUp: { from: { opacity: 0, transform: 'translateY(10px)' }, to: { opacity: 1, transform: 'translateY(0)' } },
        shimmer: { '0%': { backgroundPosition: '-200% 0' }, '100%': { backgroundPosition: '200% 0' } },
      }
    }
  },
  plugins: []
}
