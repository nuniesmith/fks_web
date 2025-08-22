import { defineConfig } from 'vitest/config.js'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    css: true,
    testTimeout: 20000, // 20 seconds max per test (reduced for CI)
    hookTimeout: 8000,  // 8 seconds max for hooks (reduced for CI)
    // Ensure tests exit cleanly in CI
    watch: false,
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/',
        'src/test/',
        '**/*.d.ts',
        '**/*.config.*',
        'src/main.tsx',
        'dist/'
      ]
    }
  },
  resolve: {
    alias: {
      '@': '/src',
      '@components': '/src/components',
      '@contexts': '/src/contexts',
      '@services': '/src/services',
      '@utils': '/src/utils',
  '@types': '/src/types',
  '@features': '/src/features',
  '@shared': '/src/shared'
    }
  }
})
