import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';
import { satteri } from '@astrojs/markdown-satteri';
import mermaid from 'astro-mermaid';
import starlightLinksValidator from 'starlight-links-validator';
import starlightLlmsTxt from 'starlight-llms-txt';
import { factsInHeadings } from './src/plugins/facts-in-headings.mjs';
import { pythonMarkdownHeadingIds } from './src/plugins/heading-ids.mjs';
import { knownBroken, scriptRoute } from './src/known-broken-links.mjs';

// https://turingpi.xyz. The pages are src/content/docs; the site's name,
// nav and footer are src/config/.
const config = (name) => JSON.parse(readFileSync(new URL(`./src/config/${name}`, import.meta.url), 'utf8'));

const site = config('site.json');

// Who serves /llms.txt -- the owner's call, so it is one line:
//   'curated'  scripts/llms.py's index (src/data/llms.txt): the nav's
//              order, one line per page.
//   'plugin'   starlight-llms-txt: its own /llms.txt, plus /llms-full.txt and
//              /llms-small.txt, the whole site as text.
// Both cannot be served: two writers of one address is a build warning.
const llmsTxt = 'curated';

/** Serves the curated /llms.txt (src/routes/llms.txt.ts). */
const curatedLlmsTxt = {
  name: 'curated-llms-txt',
  hooks: {
    'astro:config:setup': ({ injectRoute }) =>
      injectRoute({ pattern: '/llms.txt', entrypoint: './src/routes/llms.txt.ts', prerender: true }),
  },
};

// Starlight's default (prefetch every link on hover), stated here so the Vite
// plugin below fills in the same values Astro's prefetch script is configured with.
const prefetch = { prefetchAll: true, defaultStrategy: 'hover' };

// Astro's prefetch script (astro/dist/prefetch/index.js) holds the placeholders
// __PREFETCH_PREFETCH_ALL__, __PREFETCH_DEFAULT_STRATEGY__ and
// __EXPERIMENTAL_CLIENT_PRERENDER__, which Astro's `astro:prefetch` Vite plugin
// replaces in a transform hook. That hook matches the module id against the
// literal path `astro/dist/prefetch/index.js`. With `nodeLinker: pnpm`
// (site/.yarnrc.yml) the id is the real path,
// node_modules/.store/astro-virtual-<hash>/package/dist/..., which does not
// match, so the placeholders shipped. Starlight bundles every page-level
// script into one page.<hash>.js, so the ReferenceError at the top of the
// prefetch module stopped the rest of that file (prefetch's own init, and the
// whole of astro-mermaid's) from running on every page.
// This plugin does the same replacement whatever the layout. Drop it once Astro
// matches the package directory; site/scripts/check-built.sh fails the build if
// a placeholder ever ships again.
const fillPrefetchPlaceholders = () => ({
  name: 'turingpi:fill-prefetch-placeholders',
  enforce: 'pre',
  transform(code, id) {
    if (!/[\\/]dist[\\/]prefetch[\\/]index\.js(\?|$)/.test(id)) return null;
    if (!code.includes('__PREFETCH_PREFETCH_ALL__')) return null;
    return {
      code: code
        .replace('__PREFETCH_PREFETCH_ALL__', JSON.stringify(prefetch.prefetchAll))
        .replace('__PREFETCH_DEFAULT_STRATEGY__', JSON.stringify(prefetch.defaultStrategy))
        .replace('__EXPERIMENTAL_CLIENT_PRERENDER__', 'false'),
      map: null,
    };
  },
});

export default defineConfig({
  site: site.site,
  // MkDocs serves directory URLs with a trailing slash, and every inbound
  // link to this site is one of those.
  trailingSlash: 'always',
  prefetch,
  build: { format: 'directory' },
  markdown: {
    processor: satteri({
      // Before Starlight's own heading ids, which keep an id already set:
      // anchors stay the ones MkDocs wrote, so deep links keep working.
      // A <Fact> in a heading is text before the ids are written, so an
      // anchor like /why/fresh-and-fixed/#142-releases-... stays the same.
      hastPlugins: [
        factsInHeadings({ file: fileURLToPath(new URL('./src/data/facts.yaml', import.meta.url)) }),
        pythonMarkdownHeadingIds,
      ],
      // python-markdown has no smart punctuation unless asked, and this site
      // never asked: "--" stays two hyphens, as it is written.
      features: { smartPunctuation: false },
    }),
  },
  vite: {
    plugins: [fillPrefetchPlaceholders()],
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
      // Dates come from each page's git history, across renames
      // (src/content.config.ts), into its front matter.
      lastUpdated: false,
      // The 404 page is src/pages/404.astro.
      disable404Route: true,
      head: [
        // What overrides/main.html writes on every page. The per-page tags --
        // Open Graph, robots, structured data -- are src/route-data.ts.
        {
          tag: 'link',
          attrs: {
            rel: 'alternate',
            type: 'application/atom+xml',
            title: `${site.title} — firmware releases`,
            href: `${site.site}/feed.xml`,
          },
        },
      ],
      // Starlight's own look: its palette, retuned to this site's blue
      // (theme.css), its system fonts, and the few rules the site's own
      // layouts need (site.css).
      customCss: ['./src/styles/theme.css', './src/styles/site.css'],
      sidebar: config('sidebar.json'),
      routeMiddleware: './src/route-data.ts',
      // Two overrides, for what CSS and route data cannot do: the site's
      // footer (its links are how the front page reaches every section) and
      // the title (a page whose layout carries its own H1, a post's date).
      components: {
        Footer: './src/components/Footer.astro',
        PageTitle: './src/components/PageTitle.astro',
      },
      plugins: [
        // Fails the build on a broken internal link or anchor.
        starlightLinksValidator({
          // The demo panes are built at deploy from BMC-UI and are not in
          // a pull request's build; the front page's
          // hash routes are a script's; and src/known-broken-links.mjs lists
          // what the live site already serves broken.
          exclude: ({ link, slug }) =>
            /^\/demo\/(fork|fleet)(\/|$)/.test(link) ||
            scriptRoute.test(link) ||
            (knownBroken[slug] ?? []).includes(link),
        }),
        ...(llmsTxt === 'plugin'
          ? [starlightLlmsTxt({ projectName: site.title, description: site.description })]
          : []),
      ],
    }),
    ...(llmsTxt === 'curated' ? [curatedLlmsTxt] : []),
  ],
});
