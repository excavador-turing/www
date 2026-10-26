import { defineRouteMiddleware } from '@astrojs/starlight/route-data';
import { getCollection, getEntry, type CollectionEntry } from 'astro:content';
import site from './config/site.json';
import { facts } from './lib/data';
import { faqEntities } from './lib/faq';
import { format, lookup } from './lib/facts.mjs';
import { NEWS } from './lib/news';

// What Material's template (overrides/main.html, until MkDocs was retired)
// wrote into <head>, per page, and this site still writes: the <title> as
// Material wrote it, <meta robots> from the page, Open Graph and Twitter
// tags, the post's publication date, and the JSON-LD. Each value comes from
// the page's front matter, where tp.htmlTitle and tp.ogTitle say what the
// nav called the page wherever that is not the page's own title; the
// numbers and the FAQ's questions are read when the site is built.

const IMAGE = 'captures/power-control.png';
const OS = 'Turing Pi 2 BMC (Buildroot Linux, ARMv7)';
const CATEGORY = 'DeveloperApplication';

type Data = CollectionEntry<'docs'>['data'];

/** Open Graph's and the breadcrumb's name for a page. */
const ogName = (data: Data) => data.tp?.ogTitle ?? data.title;

let byFile: Map<string | undefined, CollectionEntry<'docs'>> | undefined;

export const onRequest = defineRouteMiddleware(async (context) => {
  const route = context.locals.starlightRoute;
  const url = context.url.pathname;
  // The news index's later pages (src/pages/news/page/[page].astro) speak
  // for the index; every other page that is not in the collection (the
  // 404) keeps Starlight's head.
  const paged = new RegExp(`^/${NEWS}/page/\\d+/$`).test(url);
  const index = await getEntry('docs', NEWS);
  if (!index) throw new Error(`the news index (${NEWS}) is not in the docs collection`);
  // A StarlightPage's entry is made up on the spot, not one of the collection.
  byFile ??= new Map((await getCollection('docs')).map((e) => [e.filePath, e]));
  const own = paged ? index : byFile.get(route.entry.filePath);
  if (!own) return;
  const data: Data = own.data;

  const home = url === '/';
  const post = !paged && data.date instanceof Date;
  const canonical = site.site + url;
  const t = data.tp ?? {};
  const title = home
    ? t.htmlTitle ? `${t.htmlTitle} - ${site.title}` : site.title
    : `${t.htmlTitle ?? data.title} - ${site.title}`;
  const ogTitle = home ? site.title : ogName(data);
  const ogDescription = data.description || site.description;
  const ogImage = `${site.site}/assets/${(!paged && data.image) || IMAGE}`;
  const published = post ? (data.date as Date).toISOString().slice(0, 10) : undefined;

  const jsonld: Record<string, unknown>[] = [];
  if (home) {
    jsonld.push({
      '@context': 'https://schema.org',
      '@type': 'SoftwareApplication',
      name: site.title,
      alternateName: 'Turing Pi 2 BMC firmware (excavador-turing fork)',
      applicationCategory: CATEGORY,
      operatingSystem: OS,
      softwareVersion: String(lookup(facts, 'releases.firmware.newest')),
      license: 'https://github.com/excavador-turing/BMC-Firmware/blob/hive/LICENSE',
      codeRepository: 'https://github.com/excavador-turing/BMC-Firmware',
      isAccessibleForFree: true,
      url: `${site.site}/`,
      description: ogDescription,
      image: ogImage,
    });
  } else if (post) {
    jsonld.push({
      '@context': 'https://schema.org',
      '@type': 'BlogPosting',
      headline: ogTitle,
      description: ogDescription,
      image: ogImage,
      url: canonical,
      mainEntityOfPage: canonical,
      datePublished: published,
      isPartOf: { '@type': 'Blog', name: `${site.title} news`, url: `${site.site}/${NEWS}/` },
      about: {
        '@type': 'SoftwareApplication',
        name: site.title,
        // The release the post is about: the last part of its URL, v2.44.0.
        softwareVersion: url.split('/').filter(Boolean).pop(),
        operatingSystem: OS,
        applicationCategory: CATEGORY,
      },
    });
  } else if (url === '/faq/') {
    // The questions, read off the page; each <Fact> as the number a reader
    // sees there (lib/faq.ts).
    const qs = faqEntities(route.entry.body ?? '', 'value', (of, filters) => format(facts, of, filters));
    jsonld.push({
      '@context': 'https://schema.org',
      '@type': 'FAQPage',
      url: canonical,
      mainEntity: qs.map(({ q, a }) => ({
        '@type': 'Question',
        name: q,
        acceptedAnswer: { '@type': 'Answer', text: a },
      })),
    });
  }
  if (!home) {
    // Material's ancestors: nav sections carry no URL and drop out, so a
    // page's trail is the site and itself -- except a post, whose parent is
    // the news index. (The index's later pages have none.)
    const crumbs: [string, string][] = [[site.title, `${site.site}/`]];
    if (post) crumbs.push([ogName(index.data), `${site.site}/${NEWS}/`]);
    crumbs.push([ogTitle, canonical]);
    jsonld.push({
      '@context': 'https://schema.org',
      '@type': 'BreadcrumbList',
      itemListElement: crumbs.map(([name, item], i) => ({
        '@type': 'ListItem',
        position: i + 1,
        name,
        item,
      })),
    });
  }

  const ours = (h: { tag: string; attrs?: Record<string, unknown> }) => {
    if (h.tag !== 'meta') return false;
    const property = String(h.attrs?.property ?? '');
    const name = String(h.attrs?.name ?? '');
    return property.startsWith('og:') || property.startsWith('article:') ||
      name.startsWith('twitter:') || name === 'robots';
  };
  const head = route.head.filter((h) => !ours(h));
  for (const h of head) if (h.tag === 'title') h.content = title;

  const meta = (attrs: Record<string, string>) => head.push({ tag: 'meta', attrs, content: '' });
  if (t.robots) meta({ name: 'robots', content: t.robots });
  meta({ property: 'og:site_name', content: route.siteTitle });
  meta({ property: 'og:type', content: post ? 'article' : 'website' });
  meta({ property: 'og:title', content: ogTitle });
  meta({ property: 'og:description', content: ogDescription });
  meta({ property: 'og:url', content: canonical });
  meta({ property: 'og:image', content: ogImage });
  meta({ property: 'og:locale', content: 'en' });
  if (published) meta({ property: 'article:published_time', content: published });
  meta({ name: 'twitter:card', content: 'summary_large_image' });
  meta({ name: 'twitter:title', content: ogTitle });
  meta({ name: 'twitter:description', content: ogDescription });
  meta({ name: 'twitter:image', content: ogImage });
  for (const doc of jsonld) {
    head.push({
      tag: 'script',
      attrs: { type: 'application/ld+json' },
      // "<" escaped so no string in the data can close the script element.
      content: JSON.stringify(doc).replace(/</g, '\\u003c'),
    });
  }
  route.head = head;
});
