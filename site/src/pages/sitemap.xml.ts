import type { APIRoute } from 'astro';
import { getCollection } from 'astro:content';
import { pageCount, pageUrl } from '../lib/news';

// /sitemap.xml, the address MkDocs published and robots.txt names.
// Starlight's own sitemap is /sitemap-index.xml; this one keeps the old
// address answering, with the page's last-changed date where git has one,
// and lists the news index's later pages as MkDocs's did.
export const GET: APIRoute = async ({ site }) => {
  const docs = await getCollection('docs');
  const urls = docs
    .map((d) => ({
      loc: new URL(d.id === 'index' ? '/' : `/${d.id}/`, site).href,
      lastmod: d.data.lastUpdated instanceof Date ? d.data.lastUpdated.toISOString().slice(0, 10) : undefined,
    }))
    .concat(
      Array.from({ length: (await pageCount()) - 1 }, (_, i) => ({
        loc: new URL(pageUrl(i + 2), site).href,
        lastmod: undefined,
      })),
    )
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
