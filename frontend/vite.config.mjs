import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';
import { NodeGlobalsPolyfillPlugin } from '@esbuild-plugins/node-globals-polyfill';
import path from 'path';

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  // Load env variables from `.env`, `.env.production`, etc
  const env = loadEnv(mode, process.cwd(), '');

  return {
    base: '/', // Change to '/subpath/' if app is deployed in a subdirectory
    plugins: [react()],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, 'src'), // allow @/some/path import
      },
    },
    define: {
      'process.env': {}, // prevent some polyfill-related errors
    },
    optimizeDeps: {
      esbuildOptions: {
        plugins: [NodeGlobalsPolyfillPlugin({ buffer: true })],
      },
    },
    build: {
      target: 'esnext',
      outDir: 'dist',
      minify: 'terser',
      sourcemap: false,
      rollupOptions: {
        output: {
          manualChunks: {
            vendor: ['react', 'react-dom', 'react-router-dom'],
          },
        },
      },
    },
    server: {
      port: 5173,
      strictPort: true,
      open: true,
    },
  };
});
