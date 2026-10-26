import { defineConfig } from 'astro/config';

export default defineConfig({
  site: 'https://nossodinheiro.org',
  output: 'static',
  build: { format: 'directory' },
});
