import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  darkMode: 'class',
  theme: {
    extend: {
      borderColor: {
        DEFAULT: 'var(--color-outline-variant)',
      },
      colors: {
        primary: 'var(--color-primary)',
        'on-primary': 'var(--color-on-primary)',
        surface: 'var(--color-surface)',
        'on-surface': 'var(--color-on-surface)',
        background: 'var(--color-background)',
        outline: 'var(--color-brand-outline)',
        secondary: 'var(--color-secondary)',
        error: 'var(--color-error)',
        
        // Comprehensive Stitch Light & Dark System surface levels
        'surface-lowest': 'var(--color-surface-container-lowest)',
        'surface-container-lowest': 'var(--color-surface-container-lowest)',
        'surface-low': 'var(--color-surface-container-low)',
        'surface-container': 'var(--color-surface-container)',
        'surface-high': 'var(--color-surface-container-high)',
        'surface-highest': 'var(--color-surface-container-highest)',
        'surface-container-low': 'var(--color-surface-container-low)',
        'surface-container-high': 'var(--color-surface-container-high)',
        'surface-container-highest': 'var(--color-surface-container-highest)',
        'outline-variant': 'var(--color-outline-variant)',
        'on-surface-variant': 'var(--color-on-surface-variant)',
        'panel-bg': 'var(--color-panel-bg)',
      },
      borderRadius: {
        sm: '0.5rem',
        DEFAULT: '1rem',
        md: '1.5rem',
        lg: '2rem',
        xl: '3rem',
      },
      fontFamily: {
        sans: ['var(--font-sans)', 'sans-serif'],
        mono: ['var(--font-mono)', 'monospace'],
      },
      spacing: {
        xs: '4px',
        sm: '8px',
        md: '16px',
        lg: '24px',
        xl: '40px',
      },
      keyframes: {
        'google-rotate': {
          '100%': { transform: 'rotate(360deg)' },
        },
        'google-dash': {
          '0%': { strokeDasharray: '1, 200', strokeDashoffset: '0' },
          '50%': { strokeDasharray: '89, 200', strokeDashoffset: '-35px' },
          '100%': { strokeDasharray: '89, 200', strokeDashoffset: '-124px' },
        },
        'linear-loader': {
          '0%': { left: '-40%' },
          '100%': { left: '100%' },
        },
        'cell-ripple': {
          '0%': { opacity: '0.4' },
          '50%': { opacity: '0.8' },
          '100%': { opacity: '0.4' },
        },
      },
      animation: {
        'google-rotate': 'google-rotate 2s linear infinite',
        'google-dash': 'google-dash 1.5s ease-in-out infinite',
        'linear-loader': 'linear-loader 1.5s infinite linear',
        'cell-ripple': 'cell-ripple var(--duration, 200ms) ease-out var(--delay, 0ms)',
      }
    },
  },
  plugins: [
    // Clean browser autofill Tailwind utility plugin
    function ({ addUtilities }: any) {
      addUtilities({
        '.autofill-light': {
          '&:-webkit-autofill': {
            '-webkit-box-shadow': '0 0 0px 1000px #f4f2ff inset !important', // Cohesive autofill bg
            '-webkit-text-fill-color': '#1b1b1f !important',
            'transition': 'background-color 5000s ease-in-out 0s !important',
          }
        },
        '.autofill-dark': {
          '&:-webkit-autofill': {
            '-webkit-box-shadow': '0 0 0px 1000px #141313 inset !important', // Cohesive autofill bg
            '-webkit-text-fill-color': '#e5e2e1 !important',
            'transition': 'background-color 5000s ease-in-out 0s !important',
          }
        }
      });
    }
  ],
};

export default config;
