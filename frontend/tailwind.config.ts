import type { Config } from 'tailwindcss'
import defaultTheme from 'tailwindcss/defaultTheme'

const config: Config = {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#F5F3FC',
          100: '#EBE7F9',
          200: '#D6CDF2',
          300: '#B7A8E8',
          400: '#9986DD',
          500: '#8B7EE0',
          600: '#7A6CD6',
          700: '#6354B8',
          800: '#4E3F94',
          900: '#3A2F70',
        },
        ink: '#26222F',
        muted: { DEFAULT: '#6E6A7A', light: '#9A95A8' },
        surface: '#F2F1F7',
      },
      fontFamily: {
        sans: ['Archivo', ...defaultTheme.fontFamily.sans],
        mono: ['"IBM Plex Mono"', ...defaultTheme.fontFamily.mono],
      },
    },
  },
  plugins: [],
}

export default config
