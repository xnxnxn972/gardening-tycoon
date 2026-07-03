import { defineConfig } from 'vite';

export default defineConfig({
  // Relative base so the built app works on GitHub Pages subpaths.
  base: './',
  server: {
    port: 5173,
    host: true
  }
});
