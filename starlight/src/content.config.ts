import { defineCollection } from 'astro:content';
import { glob } from 'astro/loaders';
import { docsSchema, i18nSchema } from '@astrojs/starlight/schema';
import { i18nLoader } from '@astrojs/starlight/loaders';
import { z } from 'astro/zod';
import { feature } from './lib/feature';

// src/content/docs is generated from ../docs by
// ../scripts/mkdocs-to-starlight.py; every page sets its own `slug`, which is
// the URL MkDocs serves it at (a post's file is v2.44.0.md, and Astro's own
// id would drop the dots).

export const collections = {
  docs: defineCollection({
    loader: glob({ base: 'src/content/docs', pattern: '**/[^_]*.{md,mdx}' }),
    schema: docsSchema({
      extend: z.object({
        // A news post: when it was published. The news index lists the pages
        // under news/ that carry one, newest first.
        date: z.coerce.date().optional(),
        // A feature page: what its first screen says (FeatureScreen).
        feature: feature.optional(),
        // The firmware release that first carried a feature.
        since: z.string().optional(),
        // What the converter knows about a page that Starlight has no field for.
        tp: z
          .object({
            // The page carries its own H1 inside its layout (the front page,
            // Features, News, each feature page), so Starlight's is not printed.
            hideTitle: z.boolean().default(false),
          })
          .optional(),
      }),
    }),
  }),
  i18n: defineCollection({ loader: i18nLoader(), schema: i18nSchema() }),
};
