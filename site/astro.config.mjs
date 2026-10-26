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
      // Roboto, as Material loads it (from this site, not from Google);
      // landing.css is the port of Material's extra_css; site.css is the
      // frame.
      customCss: [
        '@fontsource/roboto/300.css',
        '@fontsource/roboto/400.css',
        '@fontsource/roboto/400-italic.css',
        '@fontsource/roboto/700.css',
        '@fontsource/roboto-mono/400.css',
        './src/styles/landing.css',
        './src/styles/site.css',
      ],
      sidebar: config('sidebar.json'),
      routeMiddleware: './src/route-data.ts',
      components: {
        Footer: './src/components/Footer.astro',
        Header: './src/components/Header.astro',
        PageTitle: './src/components/PageTitle.astro',
        Sidebar: './src/components/Sidebar.astro',
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
