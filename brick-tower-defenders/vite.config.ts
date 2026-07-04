import { writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { defineConfig, type Plugin } from 'vite';

// Dev-only helper: POST a canvas dataURL to /__shot and it lands in
// .shots/shot.png — lets tooling grab game screenshots headlessly.
function shotEndpoint(): Plugin {
  return {
    name: 'shot-endpoint',
    apply: 'serve',
    configureServer(server) {
      server.middlewares.use('/__shot', (req, res) => {
        let body = '';
        req.on('data', (c) => (body += c));
        req.on('end', () => {
          const b64 = body.replace(/^data:image\/png;base64,/, '');
          writeFileSync(join(server.config.root, '.shots', 'shot.png'), Buffer.from(b64, 'base64'));
          res.end('ok');
        });
      });
    }
  };
}

export default defineConfig({
  // Relative base so the built app works on GitHub Pages subpaths.
  base: './',
  plugins: [shotEndpoint()],
  server: {
    port: 5173,
    host: true
  }
});
