// Vite Configuration for FKS Trading Systems
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { visualizer } from 'rollup-plugin-visualizer'
import path from 'path'

// Helper to derive HMR settings when running behind nginx reverse proxy:
// - Browser connects to nginx on :80 (or :443) but backend dev server listens on 3000 internally.
// - Use clientPort so websocket targets nginx public port instead of internal.
const devBaseDomain = process.env.VITE_DEV_BASE_DOMAIN || process.env.BASE_DOMAIN || 'fkstrading.test'
const hmrClientPort = Number(process.env.VITE_HMR_CLIENT_PORT) || (process.env.VITE_ENABLE_SSL === 'true' ? 443 : 80)
const hmrProtocol = (process.env.VITE_HMR_PROTOCOL || (process.env.VITE_ENABLE_SSL === 'true' ? 'wss' : 'ws')) as 'ws' | 'wss'

export default defineConfig(({ mode }) => ({
  plugins: [
    react(),
    ...(mode === 'analyze'
      ? [visualizer({ filename: 'dist/stats.html', template: 'treemap', gzipSize: true, brotliSize: true, open: false })]
      : [])
  ],
    resolve: {
      alias: {
        // Prevent bundling the Node-only googleapis package in the browser build
        googleapis: path.resolve(__dirname, 'src/shims/googleapis-browser.ts'),
  '@': path.resolve(__dirname, 'src'),
  '@features': path.resolve(__dirname, 'src/features'),
  '@shared': path.resolve(__dirname, 'src/shared'),
      },
    },
  server: {
    host: '0.0.0.0',
    port: 3000,
    // Allow connecting from specific hostnames across the LAN. Without this Vite
    // will block requests whose Host header does not match the dev server URL.
    // Add common local names plus any provided via VITE_ALLOWED_HOSTS (comma separated).
    allowedHosts: [
      'desktop', // your desktop machine hostname
      process.env.VITE_DEV_BASE_DOMAIN || 'fkstrading.test',
      // Additional hosts from env var
      ...((process.env.VITE_ALLOWED_HOSTS || '')
        .split(',')
        .map(h => h.trim())
        .filter(Boolean))
    ],
    hmr: {
      port: 3000,              // internal container port Vite listens on
      clientPort: hmrClientPort, // external (nginx) port browser should use
      protocol: hmrProtocol,
      host: devBaseDomain,     // domain the browser uses (mapped via /etc/hosts)
    },
    proxy: {
      '/api': {
        target: process.env.VITE_API_URL || 'http://fkstrading.test',
        changeOrigin: true,
        // Keep /api prefix; nginx dev-multi forwards /api -> api service
        // If you need to strip, do it at nginx.
        // rewrite: (path) => path.replace(/^\/api/, '')
      },
      '/data': {
        target: process.env.VITE_DATA_URL || 'http://fkstrading.test',
        changeOrigin: true,
      },
      '/engine': {
        target: process.env.VITE_ENGINE_URL || 'http://fkstrading.test',
        changeOrigin: true,
      },
      '/ws': {
        target: process.env.VITE_WS_URL || 'ws://fkstrading.test',
        ws: true,
        changeOrigin: true
      }
    }
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
    rollupOptions: {
      output: {
        // Enhanced chunk strategy: dedicated chunks for heavy libs, grouped commons,
        // fallback to stable per-package vendor splitting for remaining modules.
        manualChunks(id: string) {
          if (id.includes('node_modules')) {
            // Explicit heavy / high-churn libs
            if (id.includes('/node_modules/react-dom/')) return 'react-dom';
            if (id.includes('/node_modules/react/')) return 'react';
            if (id.includes('/node_modules/recharts')) return 'recharts';
            if (id.includes('/node_modules/lightweight-charts')) return 'charts-core';
            if (id.includes('/node_modules/mermaid')) return 'mermaid';
            if (id.includes('/node_modules/framer-motion')) return 'motion';
            if (id.includes('/node_modules/lucide-react')) return 'icons';
            if (id.includes('/node_modules/axios')) return 'axios';
            if (id.includes('/node_modules/socket.io-client')) return 'realtime';
            if (id.includes('/node_modules/zod')) return 'validation';
            if (id.includes('/node_modules/react-hook-form')) return 'forms';
            if (id.includes('/node_modules/react-markdown')) return 'markdown';
            if (id.includes('/node_modules/dayjs')) return 'dayjs';
            if (id.includes('/node_modules/date-fns')) return 'date-fns';
            if (id.includes('/node_modules/googleapis')) return 'googleapis';
            if (id.includes('/node_modules/google-auth-library')) return 'google-auth';

            // Generic per-package fallback (keeps vendor from becoming a mega-bundle)
            const m = id.match(/node_modules\/(?:@[^/]+\/)?[^/]+/);
            if (m) {
              const pkgName = m[0]
                .replace('node_modules/','')
                .replace(/@/g,'')
                .replace(/\//g,'-');
              return `pkg-${pkgName}`;
            }
            return 'vendor';
          }

          // Application source feature grouping
          if (id.includes('/src/features/')) {
            const m = id.match(/\/src\/features\/([A-Za-z0-9_-]+)\//);
            if (m) return `feature-${m[1]}`;
          }
          if (id.includes('/components/Trading/')) return 'trading';
          if (id.includes('/components/Analytics/')) return 'analytics';
          if (id.includes('/components/Settings/')) return 'settings';
          if (id.includes('/components/Accounts/')) return 'accounts';
          if (id.includes('/components/Portfolio/')) return 'portfolio';
          if (id.includes('/components/FKSServices/')) return 'services';
          if (id.includes('/components/AI/')) return 'ai';
          if (id.includes('/components/Milestone')) return 'milestones';
          if (id.includes('/pages/ProjectManager/')) return 'project-manager';
          return undefined;
        },
        chunkFileNames: 'assets/[name]-[hash].js',
        entryFileNames: 'assets/[name]-[hash].js',
        assetFileNames: 'assets/[name]-[hash][extname]'
      }
    }
  },
  define: {
    __APP_VERSION__: JSON.stringify(process.env.npm_package_version)
  },
  optimizeDeps: {
    include: ['react', 'react-dom', 'lightweight-charts']
  }
}))
