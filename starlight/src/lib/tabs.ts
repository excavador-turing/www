// The top-level entries of the nav as tabs: each links to the first page
// under it and is current when the page is (Material's navigation.tabs).
import type { StarlightRouteData } from '@astrojs/starlight/route-data';

type Entry = StarlightRouteData['sidebar'][number];
export type Tab = { label: string; href: string; current: boolean };

function first(e: Entry): string | undefined {
  if (e.type === 'link') return e.href;
  for (const c of e.entries) {
    const h = first(c);
    if (h) return h;
  }
  return undefined;
}

function contains(e: Entry): boolean {
  return e.type === 'link' ? e.isCurrent : e.entries.some(contains);
}

/**
 * The tabs for a page. A page in the nav makes its tab current; one that is
 * not -- a news post, a later page of the news index -- falls back to the
 * tab whose first page its URL lies under, as Material's tabs did.
 */
export function tabs(sidebar: Entry[], pathname: string): Tab[] {
  const out = sidebar.flatMap((e) => {
    const href = first(e);
    return href ? [{ label: e.label, href, current: contains(e) }] : [];
  });
  if (!out.some((t) => t.current)) {
    const under = out
      .filter((t) => t.href !== '/' && pathname.startsWith(t.href))
      .sort((a, b) => b.href.length - a.href.length)[0];
    if (under) under.current = true;
  }
  return out;
}
