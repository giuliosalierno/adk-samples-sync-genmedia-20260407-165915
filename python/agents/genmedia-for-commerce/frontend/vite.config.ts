import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  publicDir: '../assets/frontend_assets/public',
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          'vendor': ['react', 'react-dom', 'react-router-dom'],
          'mediapipe': ['@mediapipe/face_mesh', '@mediapipe/camera_utils']
        }
      }
    },
    commonjsOptions: {
      include: [/node_modules/],
      transformMixedEsModules: true
    }
  },
  optimizeDeps: {
    include: ['@mediapipe/face_mesh', '@mediapipe/camera_utils'],
    esbuildOptions: {
      target: 'es2020'
    }
  },
  server: {
    port: 3000,
    open: true,
    proxy: {
      '/api/shoes/spinning': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        configure: (proxy, _options) => {
          proxy.on('proxyReq', (proxyReq, _req, _res) => {
            proxyReq.setTimeout(600000); // 10 minutes for video generation
          });
          proxy.on('proxyRes', (proxyRes, _req, _res) => {
            proxyRes.setTimeout(600000); // 10 minutes for video generation
          });
        }
      },
      '/api/glasses': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        configure: (proxy, _options) => {
          proxy.on('proxyReq', (proxyReq, _req, _res) => {
            proxyReq.setTimeout(600000); // 10 minutes for video generation
          });
          proxy.on('proxyRes', (proxyRes, _req, _res) => {
            proxyRes.setTimeout(600000); // 10 minutes for video generation
          });
        }
      },
      '/api/clothes': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        configure: (proxy, _options) => {
          proxy.on('proxyReq', (proxyReq, _req, _res) => {
            proxyReq.setTimeout(600000); // 10 minutes for VTO generation
          });
          proxy.on('proxyRes', (proxyRes, _req, _res) => {
            proxyRes.setTimeout(600000); // 10 minutes for VTO generation
          });
        }
      },
      '/api/spinning/interpolation/other': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        configure: (proxy, _options) => {
          proxy.on('proxyReq', (proxyReq, _req, _res) => {
            proxyReq.setTimeout(600000); // 10 minutes for interpolation video generation
          });
          proxy.on('proxyRes', (proxyRes, _req, _res) => {
            proxyRes.setTimeout(600000); // 10 minutes for interpolation video generation
          });
        }
      },
      '/api/spinning/r2v/other': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        configure: (proxy, _options) => {
          proxy.on('proxyReq', (proxyReq, _req, _res) => {
            proxyReq.setTimeout(600000); // 10 minutes for R2V video generation
          });
          proxy.on('proxyRes', (proxyRes, _req, _res) => {
            proxyRes.setTimeout(600000); // 10 minutes for R2V video generation
          });
        }
      },
      '/api/other/background-changer': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        configure: (proxy, _options) => {
          proxy.on('proxyReq', (proxyReq, _req, _res) => {
            proxyReq.setTimeout(600000); // 10 minutes for background changing
          });
          proxy.on('proxyRes', (proxyRes, _req, _res) => {
            proxyRes.setTimeout(600000); // 10 minutes for background changing
          });
        }
      },
      '/api/product-enrichment/product-fitting': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        configure: (proxy, _options) => {
          proxy.on('proxyReq', (proxyReq, _req, _res) => {
            proxyReq.setTimeout(600000); // 10 minutes for product fitting
          });
          proxy.on('proxyRes', (proxyRes, _req, _res) => {
            proxyRes.setTimeout(600000); // 10 minutes for product fitting
          });
        }
      },
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        configure: (proxy, _options) => {
          proxy.on('proxyReq', (proxyReq, _req, _res) => {
            proxyReq.setTimeout(600000);
          });
          proxy.on('proxyRes', (proxyRes, _req, _res) => {
            proxyRes.setTimeout(600000);
          });
        }
      },
      '/chat': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        configure: (proxy, _options) => {
          proxy.on('proxyReq', (proxyReq, _req, _res) => {
            proxyReq.setTimeout(600000); // 10 minutes for chat
          });
          proxy.on('proxyRes', (proxyRes, _req, _res) => {
            proxyRes.setTimeout(600000); // 10 minutes for chat
          });
        }
      },
    },
  },
})
