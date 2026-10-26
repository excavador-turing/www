import { readFileSync } from 'node:fs';
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';
import { satteri } from '@astrojs/markdown-satteri';
import mermaid from 'astro-mermaid';
import starlightLinksValidator from 'starlight-links-validator';
import starlightLlmsTxt from 'starlight-llms-txt';
import { pythonMarkdownHeadingIds } from './src/plugins/heading-ids.mjs';
import { knownBroken, scriptRoute } from './src/known-broken-links.mjs';

// https://turingpi.xyz, built from the MkDocs sources in ../docs. Everything
// under src/content/docs, public/ and src/generated/ is written by
// ../scripts/mkdocs-to-starlight.py before every build, and is not committed:
// MkDocs stays the source of truth until the switch.
function generated(name) {
  const url = new URL(`./src/generated/${name}`, import.meta.url);
  try {
    return JSON.parse(readFileSync(url, 'utf8'));
  } catch (e) {
    throw new Error(
      `src/generated/${name} is missing: run scripts/mkdocs-to-starlight.py first (just site-build does)`,
      { cause: e },
    );
  }
}

const site = generated('site.json');

export default defineConfig({
  site: site.site,
  // MkDocs serves directory URLs with a trailing slash, and every inbound
  // link to this site is one of those.
  trailingSlash: 'always',
  build: { format: 'directory' },
  markdown: {
    processor: satteri({
      // Before Starlight's own heading ids, which keep an id already set:
      // anchors stay the ones MkDocs wrote, so deep links keep working.
      hastPlugins: [pythonMarkdownHeadingIds],
      // python-markdown has no smart punctuation unless asked, and this site
      // never asked: "--" stays two hyphens, as it is written in docs/.
      features: { smartPunctuation: false },
    }),
  },
  vite: {
    // Mermaid's diagram engines are one large lazily loaded chunk; the size
    // warning is expected for it and the build allows no other warning.
    build: { chunkSizeWarningLimit: 4000 },
    // Sätteri is a native module that finds its platform binary by
    // require() from its own directory. Bundled into the prerender chunks it
    // looks beside dist/ instead, where the pnpm layout has no such package,
    // and fails -- which an .mdx page (the two with tabs) reaches when
    // starlight-llms-txt renders it. So it stays external (in Astro's own
    // "prerender" environment, which `ssr.external` does not reach) and is a
    // direct dependency in package.json, so the pnpm layout can resolve it.
    environments: { prerender: { resolve: { external: ['satteri'] } } },
  },
  integrations: [
    // Must come before Starlight so ```mermaid fences are claimed first.
    // Bundled, not loaded from a CDN.
    mermaid({ theme: 'neutral', autoTheme: true, enableLog: false }),
    starlight({
      title: site.title,
      description: site.description,
      // "Page - Site", the way Material writes <title>.
      titleDelimiter: '-',
      social: [
        { icon: 'github', label: 'The code', href: 'https://github.com/excavador-turing/BMC-Firmware' },
      ],
      // Material's edit_uri is "" and it has no previous/next footer.
      pagination: false,
      // Dates come from each source file's git history, in front matter.
      lastUpdated: false,
      // The 404 page is src/pages/404.astro.
      disable404Route: true,
      head: [
        // What overrides/main.html writes on every page, and the stylesheet
        // mkdocs.yml loads with extra_css. The per-page tags -- Open Graph,
        // robots, structured data -- are src/route-data.ts.
        {
          tag: 'link',
          attrs: {
            rel: 'alternate',
            type: 'application/atom+xml',
            title: `${site.title} — firmware releases`,
            href: `${site.site}/feed.xml`,
          },
        },
        { tag: 'link', attrs: { rel: 'stylesheet', href: '/stylesheets/landing.css' } },
      ],
      customCss: ['./src/styles/site.css'],
      sidebar: generated('sidebar.json'),
      routeMiddleware: './src/route-data.ts',
      components: {
        Footer: './src/components/Footer.astro',
        PageTitle: './src/components/PageTitle.astro',
      },
      plugins: [
        // Fails the build on a broken internal link or anchor.
        starlightLinksValidator({
          // The demo panes are built at deploy from BMC-UI and are not in
          // this build (nor in MkDocs's on a pull request); the front page's
          // hash routes are a script's; and src/known-broken-links.mjs lists
          // what the live site already serves broken.
          exclude: ({ link, slug }) =>
            /^\/demo\/(fork|fleet)(\/|$)/.test(link) ||
            scriptRoute.test(link) ||
            (knownBroken[slug] ?? []).includes(link),
        }),
        starlightLlmsTxt({
          projectName: site.title,
          description: site.description,
        }),
      ],
    }),
  ],
});
