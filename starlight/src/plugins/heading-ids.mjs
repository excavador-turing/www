// Heading ids the way python-markdown's toc extension writes them, so every
// anchor on turingpi.xyz -- in a search result, a chat message, another page
// of this site -- still lands where it did under MkDocs.
//
// Starlight's own ids come from github-slugger, which disagrees on exactly
// the headings this site likes: "Upstream, and this fork" is the same in
// both, but "A — B" is "a-b" here and "a--b" there, and a repeated heading
// is "x_1" here and "x-1" there. This runs first; Starlight keeps an id that
// is already set.
//
// markdown.extensions.toc.slugify (unicode=False) and toc.unique, ported.

export function slugify(value) {
  const ascii = value.normalize('NFKD').replace(/[^\x00-\x7f]/g, '');
  return ascii
    .replace(/[^\w\s-]/g, '')
    .trim()
    .toLowerCase()
    .replace(/[-\s]+/g, '-');
}

export function unique(id, ids) {
  while (ids.has(id) || !id) {
    const m = /^(.*)_([0-9]+)$/.exec(id);
    id = m ? `${m[1]}_${Number(m[2]) + 1}` : `${id}_1`;
  }
  ids.add(id);
  return id;
}

/** A Sätteri hast plugin factory: one id set per document. */
export function pythonMarkdownHeadingIds() {
  const ids = new Set();
  return {
    name: 'python-markdown-heading-ids',
    element: {
      filter: ['h1', 'h2', 'h3', 'h4', 'h5', 'h6'],
      visit(node, ctx) {
        const existing = node.properties?.id;
        if (typeof existing === 'string' && existing) {
          ids.add(existing);
          return;
        }
        ctx.setProperty(node, 'id', unique(slugify(ctx.textContent(node)), ids));
      },
    },
  };
}
