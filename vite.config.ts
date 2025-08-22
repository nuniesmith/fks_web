// Vite Configuration for FKS Trading Systems
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// Helper to derive HMR settings when running behind nginx reverse proxy:
// - Browser connects to nginx on :80 (or :443) but backend dev server listens on 3000 internally.
// - Use clientPort so websocket targets nginx public port instead of internal.
const devBaseDomain = process.env.VITE_DEV_BASE_DOMAIN || process.env.BASE_DOMAIN || 'fkstrading.test'
const hmrClientPort = Number(process.env.VITE_HMR_CLIENT_PORT) || (process.env.VITE_ENABLE_SSL === 'true' ? 443 : 80)
const hmrProtocol = (process.env.VITE_HMR_PROTOCOL || (process.env.VITE_ENABLE_SSL === 'true' ? 'wss' : 'ws')) as 'ws' | 'wss'

export default defineConfig({
  plugins: [react()],
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
        // More granular chunk strategy: keep core libs minimal and split feature domains & heavy libs.
        manualChunks(id: string) {
          // Normalize path for consistency
          const isModule = id.includes('node_modules');
          if (isModule) {
            // Core framework splits
            if (id.includes('/node_modules/react-dom/')) return 'react-dom';
            if (id.includes('/node_modules/react/')) return 'react';

            // Time/date libs
            if (id.includes('/node_modules/date-fns')) return 'date-fns';
            // moment removed (replaced by dayjs) – keep mapping for any stray transitive
            if (id.includes('/node_modules/moment')) return 'legacy-moment';
            if (id.includes('/node_modules/dayjs')) return 'dayjs';

            // Charts & visualization
            if (id.includes('lightweight-charts')) return 'charts-core';
            if (id.match(/chart\.js/)) return 'chartjs';
            if (id.match(/recharts/)) return 'recharts';

            // UI / motion / icons
            if (id.includes('lucide-react')) return 'icons';
            if (id.includes('framer-motion')) return 'motion';

            // Markdown / text processing
            if (id.includes('react-markdown')) return 'markdown';

            // Forms & validation
            if (id.match(/react-hook-form/)) return 'forms';
            if (id.match(/zod/)) return 'validation';

            // Realtime / sockets
            if (id.includes('socket.io-client')) return 'realtime';

            // Fallback vendor bucket
            return 'vendor';
          }

            // Feature-based application source splitting
            if (id.includes('/src/features/')) {
              const m = id.match(/\/src\/features\/(\w+)\//);
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
})
