// The FAQ's structured data: every "## question" with the first paragraph
// under it, as MkDocs's main.py once read it.
//
// Read off the page itself when the site is built (the route middleware
// calls this with the FAQ's own source), so it follows the page with nothing
// to regenerate. Capped, because a rich result shows two lines of an answer;
// an answer that is a table, a list or a code block is left out rather than
// flattened into nonsense.
const CAP = 600;

export type Entity = { q: string; a: string };

/**
 * The questions and their answers, each <Fact> as the number a reader sees
 * on the page. (MkDocs's FAQPage carried the raw `{{ roadmap.count }}`: its
 * main.py read faq.md before the macros rendered it.)
 */
export function faqEntities(
  source: string,
  value: (of: string, filters: string) => string,
): Entity[] {
  const text = source.replace(/<Fact of="([^"]+)"(?: filters="([^"]*)")? \/>/g, (_, of: string, filters = '') =>
    value(of, filters),
  );
  const out: Entity[] = [];
  const heads = [...text.matchAll(/^## +(.+?)\s*$/gm)];
  for (const [i, m] of heads.entries()) {
    const question = m[1]!.trim();
    const end = heads[i + 1]?.index ?? text.length;
    const body = text.slice(m.index! + m[0].length, end);
    const answer: string[] = [];
    for (const line of body.split('\n')) {
      const s = line.trim();
      if (!s) {
        if (answer.length) break; // the first paragraph is the answer
        continue;
      }
      if (/^(#|\||```|!!!|\?\?\?|<|\{|- |\* |:)/.test(s)) break;
      answer.push(s);
    }
    let a = answer.join(' ');
    a = a.replace(/!?\[([^\]]*)\]\([^)]*\)/g, '$1');
    a = a.replace(/[*`]+/g, '');
    a = a.split(/\s+/).filter(Boolean).join(' ');
    if (a.length < 40) continue; // not an answer, whatever it is
    if (a.length > CAP) a = a.slice(0, CAP).replace(/ [^ ]*$/, '') + '…';
    out.push({ q: question, a });
  }
  return out;
}
