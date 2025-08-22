// PostCSS config pinned to Tailwind CSS v3 (stable during migration)
// If upgrading to v4 later, reintroduce @tailwindcss/postcss.
module.exports = {
  plugins: [
    require('tailwindcss'),
    require('autoprefixer')
  ]
}
