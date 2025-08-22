// Tailwind CSS v4+ PostCSS config (ESM). Ensure you have installed:
//   npm install -D @tailwindcss/postcss autoprefixer
// If @tailwindcss/postcss isn't installed yet, the dev server will log a warning.

import autoprefixer from 'autoprefixer'

let tailwindModule
try {
  tailwindModule = await import('@tailwindcss/postcss')
} catch (e) {
  try {
    // Fallback for legacy tailwindcss < v4 if still present
    tailwindModule = await import('tailwindcss')
    console.warn('[postcss.config] Using legacy tailwindcss package; install @tailwindcss/postcss for v4+')
  } catch (e2) {
    console.warn('[postcss.config] Tailwind plugin not found. Install @tailwindcss/postcss')
  }
}

const tailwindPlugin = typeof tailwindModule === 'function'
  ? tailwindModule
  : (tailwindModule?.default || tailwindModule)

export default {
  plugins: [
    tailwindPlugin && (typeof tailwindPlugin === 'function' ? tailwindPlugin() : tailwindPlugin),
    autoprefixer()
  ].filter(Boolean)
}
