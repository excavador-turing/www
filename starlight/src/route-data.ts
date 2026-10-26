import { defineRouteMiddleware } from '@astrojs/starlight/route-data';
import seoData from './generated/seo.json';
import { facts } from './lib/data';
import { faqEntities } from './lib/faq';
import { format, lookup } from './lib/facts.mjs';

// What overrides/main.html writes into <head>, per page: the <title> as
// Material writes it, <meta robots> from the page, Open Graph and Twitter
// tags, the post's publication date, and the JSON-LD. The converter
// computes each value the way the template does (src/generated/seo.json);
// this only puts them in place of Starlight's defaults for the same tags.
//
// Two parts are not the converter's but read live when the site is built,
// so they follow their data with nothing to regenerate: the front page's
// softwareVersion (facts.yaml) and the FAQ's questions (the FAQ page itself).

type Seo = {
  title: string;
  robots?: string;
  ogType: string;
  ogTitle: string;
  ogDescription: string;
  ogUrl: string;
  ogImage: string;
  published?: string;
  jsonld?: unknown[];
};

const seo = seoData as Record<string, Seo>;

export const onRequest = defineRouteMiddleware((context) => {
  const route = context.locals.starlightRoute;
  const page = seo[context.url.pathname];
  if (!page) return;

  const ours = (h: { tag: string; attrs?: Record<string, unknown> }) => {
    if (h.tag !== 'meta') return false;
    const property = String(h.attrs?.property ?? '');
    const name = String(h.attrs?.name ?? '');
    return property.startsWith('og:') || property.startsWith('article:') ||
      name.startsWith('twitter:') || name === 'robots';
  };
  const head = route.head.filter((h) => !ours(h));
  for (const h of head) if (h.tag === 'title') h.content = page.title;

  const meta = (attrs: Record<string, string>) => head.push({ tag: 'meta', attrs, content: '' });
  if (page.robots) meta({ name: 'robots', content: page.robots });
  meta({ property: 'og:site_name', content: route.siteTitle });
  meta({ property: 'og:type', content: page.ogType });
  meta({ property: 'og:title', content: page.ogTitle });
  meta({ property: 'og:description', content: page.ogDescription });
  meta({ property: 'og:url', content: page.ogUrl });
  meta({ property: 'og:image', content: page.ogImage });
  meta({ property: 'og:locale', content: 'en' });
  if (page.published) meta({ property: 'article:published_time', content: page.published });
  meta({ name: 'twitter:card', content: 'summary_large_image' });
  meta({ name: 'twitter:title', content: page.ogTitle });
  meta({ name: 'twitter:description', content: page.ogDescription });
  meta({ name: 'twitter:image', content: page.ogImage });
  for (const doc of live(page.jsonld ?? [], route.entry.body ?? '')) {
    head.push({
      tag: 'script',
      attrs: { type: 'application/ld+json' },
      // "<" escaped so no string in the data can close the script element.
      content: JSON.stringify(doc).replace(/</g, '\\u003c'),
    });
  }
  route.head = head;
});

/** The structured data, with what is read when the site is built filled in. */
function live(jsonld: unknown[], body: string): unknown[] {
  return jsonld.map((d) => {
    const doc = d as Record<string, unknown>;
    if (doc['@type'] === 'SoftwareApplication' && 'softwareVersion' in doc) {
      return { ...doc, softwareVersion: String(lookup(facts, 'releases.firmware.newest')) };
    }
    if (doc['@type'] === 'FAQPage') {
      // 'jinja': as the live site serves it today (see lib/faq.ts).
      const qs = faqEntities(body, 'jinja', (of, filters) => format(facts, of, filters));
      return {
        ...doc,
        mainEntity: qs.map(({ q, a }) => ({
          '@type': 'Question',
          name: q,
          acceptedAnswer: { '@type': 'Answer', text: a },
        })),
      };
    }
    return doc;
  });
}
