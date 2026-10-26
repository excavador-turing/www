// Links that are broken on the LIVE site today, kept out of the links
// validator so the strict build stays strict for everything else.
//
// Every one of these is a relative URL in raw HTML, written for a page at a
// different depth than the one it is on -- `href="features/"` on /faq/,
// `href="../guides/install/"` on /why/<page>/, the Features index's plates
// (main.py feature_plates) pointing at /<feature>/ -- which MkDocs passes
// through unchecked: `mkdocs build --strict` validates Markdown links only. Each answers 404 on https://turingpi.xyz as of 2026-10-26.
//
// They are not fixed here: phase 1 changes nothing that is live, and the fix
// is in docs/, where it changes the MkDocs site too. When one is fixed there,
// delete its line; starlight/scripts/check-built.sh fails while a line names
// a page that now exists, so this list can only shrink.

/** Front-page routes a script handles (#overview, #demo/<pane>): never ids. */
export const scriptRoute = /^\/?#(overview|demo(\/(fork|fleet|stock))?)$/;

/** slug -> links on that page that the live site serves broken. */
export const knownBroken = {
  "faq": [
    "/faq/features/",
    "/faq/guides/install/",
    "/faq/reference/known-faults/",
    "/faq/roadmap/",
  ],
  "roadmap": [
    "/roadmap/features/",
    "/roadmap/feedback/",
    "/roadmap/news/",
    "/roadmap/news/v2.40.0/",
    "/roadmap/news/v2.41.0/",
    "/roadmap/news/v2.42.0/",
    "/roadmap/news/v2.43.0/",
    "/roadmap/news/v2.44.0/",
    "/roadmap/reference/known-faults/",
  ],
  "changelog": [
    "/bmc-ui/",
    "/bmcd/",
    "/firmware/",
    "/tpi/",
  ],
  "features": [
    "/a-certificate-that-does-not-rot/",
    "/a-console-to-every-module/",
    "/flash-from-the-card/",
    "/fresh-and-fixed/",
    "/one-page-over-every-board/",
    "/pick-a-version/",
    "/see-what-the-board-sees/",
    "/the-board-describes-itself/",
    "/update-without-touching-your-nodes/",
    "/updates-that-undo-themselves/",
    "/who-may-reach-this-board/",
  ],
  "why/a-certificate-that-does-not-rot": [
    "/why/#demo/fork",
    "/why/guides/install/",
    "/why/reference/known-faults/",
  ],
  "why/a-console-to-every-module": [
    "/why/#demo/fork",
    "/why/reference/cli/",
    "/why/reference/known-faults/",
  ],
  "why/flash-from-the-card": [
    "/why/#demo/fork",
    "/why/reference/api/storage/",
    "/why/reference/cli/",
  ],
  "why/fresh-and-fixed": [
    "/why/#demo/fork",
    "/why/guides/upgrade-from-stock/",
    "/why/reference/comparison/",
  ],
  "why/one-page-over-every-board": [
    "/why/#demo/fleet",
    "/why/guides/install/",
    "/why/reference/known-faults/",
  ],
  "why/pick-a-version": [
    "/why/#demo/fork",
    "/why/guides/upgrade-from-stock/",
    "/why/reference/comparison/",
  ],
  "why/see-what-the-board-sees": [
    "/why/#demo/fork",
    "/why/guides/monitor-it/",
    "/why/reference/metrics/",
  ],
  "why/the-board-describes-itself": [
    "/why/#demo/fork",
    "/why/demo/fork/",
    "/why/reference/api/",
    "/why/reference/cli/",
  ],
  "why/updates-that-undo-themselves": [
    "/why/#demo/fork",
    "/why/guides/install/",
    "/why/reference/gate-history/",
  ],
  "why/update-without-touching-your-nodes": [
    "/why/#demo/fork",
    "/why/guides/upgrade-from-stock/",
    "/why/reference/comparison/",
  ],
  "why/who-may-reach-this-board": [
    "/why/#demo/fork",
    "/why/guides/install/",
    "/why/reference/known-faults/",
  ],
};
