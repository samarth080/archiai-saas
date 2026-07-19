import type { Config } from 'tailwindcss'
import defaultTheme from 'tailwindcss/defaultTheme'

// ArchiAI design tokens — dark ash-gray / graphite system with white as the
// primary accent. One consistent product layout: the website pages, the
// editor chrome, and the canvases all draw from this single scale.
const config: Config = {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        graphite: {
          950: '#0E0F11', // deepest — editor grid wells
          900: '#131417', // app background
          850: '#17191C', // page section alternation
          800: '#1C1E22', // panels
          750: '#212327', // raised panels / hover surfaces
          700: '#26282D', // inputs
          600: '#31343A', // strong borders / disabled surfaces
          500: '#43464C', // disabled text on panels
          400: '#5C6067',
          300: '#8A8E95',
          200: '#B9BCC1',
          100: '#DDDEE1',
          50: '#F3F4F5',
        },
        // Semantic tokens (dark theme): ink = primary text, muted = secondary,
        // muted-light = tertiary/disabled, surface = app background.
        ink: '#F3F4F5',
        muted: { DEFAULT: '#A2A6AD', light: '#75797F' },
        surface: '#131417',
        // Status colors, deliberately muted per the approved direction.
        ok: '#8FAE94',
        warn: '#C9A96E',
        danger: '#C97B70',
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
