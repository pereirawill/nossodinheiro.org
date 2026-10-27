import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';

export default defineConfig({
  site: 'https://nossodinheiro.org',
  output: 'static',
  build: { format: 'directory' },
  integrations: [
    sitemap({
      // Páginas de município (≈5.600) com prioridade menor; painéis com maior.
      serialize(item) {
        const u = item.url;
        if (/\/municipios\/[a-z]{2}\/[^/]+\/$/.test(u)) { item.priority = 0.4; item.changefreq = 'monthly'; }
        else if (/\/(uf|partido)\//.test(u)) { item.priority = 0.6; item.changefreq = 'weekly'; }
        else { item.priority = 0.9; item.changefreq = 'daily'; }
        return item;
      },
    }),
  ],
});
