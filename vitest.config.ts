import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    css: true,
    watch: false,
    coverage: {
      provider: 'v8',
      reporter: ['text','json','html'],
      exclude: ['node_modules/','src/test/','**/*.d.ts','**/*.config.*','src/main.tsx','dist/']
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
  '@shared': '/src/shared',
  '@layout': '/src/components/layout',
  '@stats': '/src/components/stats',
  '@providers': '/src/context'
    }
  }
});
