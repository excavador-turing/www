// The blog: the posts under news/, in the order the news index lists them.
//
// Not starlight-blog. It serves its index pages at /<prefix>/2/, where this
// site's are /news/page/2/ (Material's blog plugin) and every one of them is
// linked from somewhere; it overrides MarkdownContent, injects its own RSS
// feed and structured data next to the ones this site already serves; and it
// would take /news/ itself, which is a written page here. What it would add
// -- authors, tags -- the MkDocs blog has switched off (mkdocs.yml: authors,
// categories: false). So the blog is the posts plus PostList and one route.
import { getCollection, type CollectionEntry } from 'astro:content';

export type Post = CollectionEntry<'docs'> & { data: { date: Date } };

/** Posts per page of the news index, as MkDocs's blog plugin paged it. */
export const POSTS_PER_PAGE = 10;

export const NEWS = 'news';

let cache: Post[] | undefined;

/**
 * Every post, newest first. Two posts of one day keep the order of their
 * file names, as the blog plugin's stable sort over MkDocs' walk does: the
 * index has listed v2.43.0 above v2.44.0 since they shipped on one day.
 */
export async function posts(): Promise<Post[]> {
  if (cache) return cache;
  const all = await getCollection(
    'docs',
    (e) => e.id.startsWith(`${NEWS}/`) && e.data.date instanceof Date,
  );
  cache = (all as Post[]).sort(
    (a, b) =>
      b.data.date.getTime() - a.data.date.getTime() ||
      (a.id < b.id ? -1 : a.id > b.id ? 1 : 0),
  );
  return cache;
}

export async function pageCount(): Promise<number> {
  return Math.max(1, Math.ceil((await posts()).length / POSTS_PER_PAGE));
}

export function postUrl(post: Post): string {
  return `/${post.id}/`;
}

/** The index's own URL for page n: /news/, then /news/page/2/ and on. */
export function pageUrl(n: number): string {
  return n === 1 ? `/${NEWS}/` : `/${NEWS}/page/${n}/`;
}

const MONTHS =
  'January February March April May June July August September October November December'.split(' ');

/** "15 October 2026": the blog plugin's `post_date_format: d MMMM yyyy`. */
export function humanDate(d: Date): string {
  return `${d.getUTCDate()} ${MONTHS[d.getUTCMonth()]} ${d.getUTCFullYear()}`;
}

export function isoDate(d: Date): string {
  return d.toISOString().slice(0, 10);
}
