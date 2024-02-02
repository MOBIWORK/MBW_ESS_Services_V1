import path from 'path';
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// ----------------------------------------------------------------------

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: [
      {
        find: /^~(.+)/,
        replacement: path.join(process.cwd(), 'node_modules/$1'),
      },
      {
        find: /^src(.+)/,
        replacement: path.join(process.cwd(), 'src/$1'),
      },
    ],
  },
  server: {
    port: 8035,
  },
  preview: {
    port: 8035,
  },
  build: {
    outDir: `../mbw_service_v2/public/mbw_fe`,
    emptyOutDir: true,
    target: 'es2021',
    commonjsOptions: {
      include: [/node_modules/],
    },
  },
  optimizeDeps: {
    include: ['feather-icons', 'showdown'],
  },
});
