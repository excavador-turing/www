import type { APIRoute } from 'astro';
import { getCollection } from 'astro:content';

// /sitemap.xml, the address MkDocs publishes and docs/robots.txt names.
// Starlight's own sitemap is /sitemap-index.xml; this one keeps the old
// address answering, with the page's last-changed date where git has one.
export const GET: APIRoute = async ({ site }) => {
  const docs = await getCollection('docs');
  const urls = docs
    .map((d) => ({
      loc: new URL(d.id === 'index' ? '/' : `/${d.id}/`, site).href,
      lastmod: d.data.lastUpdated instanceof Date ? d.data.lastUpdated.toISOString().slice(0, 10) : undefined,
    }))
    .sort((a, b) => a.loc.localeCompare(b.loc));
  const body = [
    '<?xml version="1.0" encoding="UTF-8"?>',
    '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ...urls.map(
      (u) => `  <url><loc>${u.loc}</loc>${u.lastmod ? `<lastmod>${u.lastmod}</lastmod>` : ''}</url>`,
    ),
    '</urlset>',
    '',
  ].join('\n');
  return new Response(body, { headers: { 'Content-Type': 'application/xml' } });
};
