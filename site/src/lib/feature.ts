import { z } from 'astro/zod';

// YAML writes a date as a date and a quoted one as a string; a proof's
// `as_of` is printed as written, so both come out as YYYY-MM-DD.
const day = z.union([z.string(), z.date()]).transform((v) =>
  v instanceof Date ? v.toISOString().slice(0, 10) : v,
);

const link = z.object({ href: z.string(), text: z.string(), note: z.string() });

// A feature page's first screen, rendered by FeatureScreen and listed by
// FeaturePlates. scripts/feature-lint.py checks the content (lede length,
// three dated proofs, four next links); this checks the shape.
export const feature = z.object({
  title: z.string().optional(),
  order: z.number().default(99),
  icon: z.string().default(''),
  summary: z.string().default(''),
  lede: z.string().default(''),
  capture: z.string().default(''),
  alt: z.string().optional(),
  caption: z.string().default(''),
  proofs: z
    .array(
      z.object({
        n: z.union([z.string(), z.number()]).transform(String),
        of: z.string(),
        source: z.string().default(''),
        as_of: day.default(''),
      }),
    )
    .default([]),
  next: z
    .object({
      demo: link.optional(),
      do: link.optional(),
      evidence: link.optional(),
      related: link.optional(),
    })
    .default({}),
});

export type Feature = z.infer<typeof feature>;
