// A <Fact> inside a heading becomes its text at compile time.
//
// Everywhere else <Fact> is a component and renders when the page does. A
// heading is different: its id is computed from its text before any
// component renders (heading-ids.mjs), and so are the table of contents and
// the search index. "## <Fact of="releases.total" /> releases" would get the
// id `releases` and a contents entry " releases", where MkDocs wrote
// `142-releases` -- an anchor the live site serves today. So in a heading,
// and only there, the value is put in as text, read from the same
// facts.yaml with the same filters (src/lib/facts.mjs). Runs before
// heading-ids.mjs.
//
// The text, but not the id. A heading that quotes a fact gets an id from its
// words alone: "## <Fact of="releases.total" /> releases, and a count" is
// `releases-and-a-count`, not `145-releases-and-a-count`. MkDocs wrote the
// value into the anchor, and so every release moved it -- six anchors had to
// leave site/served-urls.json by hand (0e442f4) for exactly that. An id that
// does not change with the number is one the permanent-URL list can keep.
import { readFileSync } from 'node:fs';
import { format, parseFacts } from '../lib/facts.mjs';
import { slugify } from './heading-ids.mjs';

const HEADINGS = new Set(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']);

function attr(node, name) {
  const a = node.attributes?.find((x) => x.type === 'mdxJsxAttribute' && x.name === name);
  if (a && typeof a.value !== 'string') {
    throw new Error(`<Fact ${name}={...}> in a heading: write ${name}="..."`);
  }
  return a?.value;
}

/** @param {{ file: string }} options  the path of facts.yaml */
export function factsInHeadings({ file }) {
  return () => {
    let facts;
    return {
      name: 'facts-in-headings',
      mdxJsxTextElement: {
        filter: ['Fact'],
        visit(node, ctx) {
          let up = ctx.parent(node);
          while (up && !(up.type === 'element' && HEADINGS.has(up.tagName))) {
            up = up.type === 'root' ? undefined : ctx.parent(up);
          }
          if (!up) return;
          // The first <Fact> met in a heading names its id, from the heading's
          // text before any fact is put in. (Heading-ids keeps an id set.)
          if (!up.properties?.id) {
            const id = slugify(ctx.textContent(up));
            if (id) ctx.setProperty(up, 'id', id);
          }
          // Read per document, so the dev server sees a refreshed file.
          facts ??= parseFacts(readFileSync(file, 'utf8'));
          ctx.replaceNode(node, { type: 'text', value: format(facts, attr(node, 'of'), attr(node, 'filters') ?? '') });
        },
      },
    };
  };
}
