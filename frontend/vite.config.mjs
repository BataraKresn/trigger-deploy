import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';
import { NodeGlobalsPolyfillPlugin } from '@esbuild-plugins/node-globals-polyfill';
import path from 'path';

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');

  return {
    base: '/',
    plugins: [react()],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, 'src'),
        '@components': path.resolve(__dirname, 'src/components'),
        '@pages': path.resolve(__dirname, 'src/pages'),
      },
    },
    define: {
      'process.env': {},
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
        input: path.resolve(__dirname, 'index.html'),
        onwarn(warning, warn) {
          console.warn('⚠️ Rollup warning:', warning.message);
        },
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
