// Links that the LIVE site serves broken, kept out of the links validator so
// the strict build stays strict for everything else.
//
// There were 62 on 2026-10-26, each a relative URL in raw HTML written for a
// page at a different depth than the one it was on (`href="features/"` on
// /faq/, the Features index's plates pointing at /<feature>/). MkDocs passes
// raw HTML through unchecked: `mkdocs build --strict` validates Markdown
// links only. All 62 were fixed at the source -- main.py, the refresh
// scripts and docs/ -- by linking from the site root, so the list is empty.
//
// The mechanism stays. Add a line only for a link the live site really
// serves broken; delete it when it is fixed, because
// starlight/scripts/check-built.sh fails while a line names a page that now
// exists, so this list can only shrink. Beside it, `just links-internal`
// fails on any internal link in the built HTML that lands on nothing.

/** Front-page routes a script handles (#overview, #demo/<pane>): never ids. */
export const scriptRoute = /^\/?#(overview|demo(\/(fork|fleet|stock))?)$/;

/** slug -> links on that page that the live site serves broken. */
export const knownBroken = {};
