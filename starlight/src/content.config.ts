import { execFileSync } from 'node:child_process';
import { dirname } from 'node:path';
import { defineCollection } from 'astro:content';
import { glob } from 'astro/loaders';
import type { Loader } from 'astro/loaders';
import { docsSchema, i18nSchema } from '@astrojs/starlight/schema';
import { i18nLoader } from '@astrojs/starlight/loaders';
import { z } from 'astro/zod';
import { feature } from './lib/feature';

// Every page sets its own `slug`, which is the URL it has always been served
// at (a post's file is v2.44.0.md, and Astro's own id would drop the dots).

// A commit that moves or rewrites pages without changing what they say --
// the move out of docs/ when MkDocs was retired, a rename of this
// directory -- ends its message with the trailer `Dates-Unchanged: yes`,
// and no page counts it as an update.
//
// Filtered here, not by `git log --invert-grep`: that drops the commit
// before --follow sees its rename, and the history stops there.

/** The day the page last changed: its newest commit, across renames,
 *  without the trailer. None for a file git does not know. */
function lastChanged(file: string): Date | undefined {
  try {
    const log = execFileSync(
      'git',
      ['log', '--follow', '--format=%cs %(trailers:key=Dates-Unchanged,valueonly,separator=%x2C)', '--', file],
      { cwd: dirname(file), encoding: 'utf8' },
    );
    const day = log
      .split('\n')
      .map((line) => line.trim().split(' '))
      .find(([d, unchanged]) => d && unchanged !== 'yes')?.[0];
    return day ? new Date(`${day}T00:00:00Z`) : undefined;
  } catch {
    return undefined;
  }
}

/** The glob loader, with each page's `lastUpdated` read from git before the
 *  schema sees it. A page that sets its own keeps it. */
function datedGlob(options: Parameters<typeof glob>[0]): Loader {
  const inner = glob(options);
  return {
    ...inner,
    load: (context) =>
      inner.load({
        ...context,
        parseData: (props) =>
          context.parseData({
            ...props,
            data: {
              ...props.data,
              lastUpdated: props.data.lastUpdated ?? (props.filePath && lastChanged(props.filePath)),
            },
          }),
      }),
  };
}

export const collections = {
  docs: defineCollection({
    loader: datedGlob({ base: 'src/content/docs', pattern: '**/[^_]*.{md,mdx}' }),
    schema: docsSchema({
      extend: z.object({
        // A news post: when it was published. The news index lists the pages
        // under news/ that carry one, newest first.
        date: z.coerce.date().optional(),
        // The Open Graph picture, a path under /assets/ (src/route-data.ts).
        image: z.string().optional(),
        // A feature page: what its first screen says (FeatureScreen).
        feature: feature.optional(),
        // The firmware release that first carried a feature.
        since: z.string().optional(),
        // What this site knows about a page that Starlight has no field for.
        tp: z
          .object({
            // The page carries its own H1 inside its layout (the front page,
            // Features, News, each feature page), so Starlight's is not printed.
            hideTitle: z.boolean().default(false),
            // <title>, where it is not the page's title: the nav says
            // "Changelogs" where the page says "Every component's changelog".
            htmlTitle: z.string().optional(),
            // Open Graph's and the breadcrumb's name, where it is not the
            // page's title: the nav's label for it.
            ogTitle: z.string().optional(),
            // <meta name="robots">.
            robots: z.string().optional(),
          })
          .optional(),
      }),
    }),
  }),
  i18n: defineCollection({ loader: i18nLoader(), schema: i18nSchema() }),
};
