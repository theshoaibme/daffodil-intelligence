import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
    '../web/src/**/*.{js,ts,jsx,tsx}',
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
    },
  },
  plugins: [],
};

export default config;
