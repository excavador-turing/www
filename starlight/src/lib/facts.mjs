// The facts every page may quote, and the two ways a page asks for one.
//
// Plain JavaScript with no Vite in it, because two very different callers
// need the same answer: the components (src/components/macros/Fact.astro),
// at render time, and the heading-id plugin (src/plugins/heading-ids.mjs),
// at compile time, which runs inside astro.config.mjs before Vite exists.
//
// The facts themselves are src/data/facts.yaml, which scripts/facts.py
// writes. Until the switch the converter copies it there from docs/data/;
// after it, facts.py writes it there and nothing else changes.
import { parse } from 'yaml';

// Eleven reads better than 11 at the top of a page (main.py's title_number).
const NUMBER_WORDS = (
  'zero one two three four five six seven eight nine ten eleven twelve thirteen ' +
  'fourteen fifteen sixteen seventeen eighteen nineteen twenty'
).split(' ');

/** facts.yaml's text -> the facts object. */
export function parseFacts(text) {
  return parse(text) ?? {};
}

/** `releases.firmware.newest` -> its value; a missing name is an error. */
export function lookup(facts, path) {
  let v = facts;
  for (const key of path.split('.')) {
    if (v === null || typeof v !== 'object' || !(key in v)) {
      throw new Error(`facts.yaml has no ${path} (stopped at ${key})`);
    }
    v = v[key];
  }
  return v;
}

/**
 * The filters a page may apply, in the order it names them: the same names
 * the Jinja macros used, so `{{ x | title_number | lower }}` is
 * `<Fact of="x" filters="title_number lower" />`.
 */
const FILTERS = {
  title_number(v) {
    const n = Number.parseInt(String(v), 10);
    const word = n >= 0 && n < NUMBER_WORDS.length ? NUMBER_WORDS[n] : String(n);
    return word.charAt(0).toUpperCase() + word.slice(1);
  },
  lower: (v) => String(v).toLowerCase(),
  // `.split()[0]`: "6.12.109 LTS" -> "6.12.109".
  first_word: (v) => String(v).trim().split(/\s+/)[0],
};

export function format(facts, path, filters = '') {
  let v = lookup(facts, path);
  for (const name of filters.split(/\s+/).filter(Boolean)) {
    const f = FILTERS[name];
    if (!f) throw new Error(`<Fact filters="${filters}">: no filter named ${name}`);
    v = f(v);
  }
  if (v !== null && typeof v === 'object') {
    throw new Error(`facts.yaml ${path} is not a single value`);
  }
  // YAML reads an unquoted 2026-09-12 as a date; the page wants it as written.
  if (v instanceof Date) return v.toISOString().slice(0, 10);
  return String(v);
}

/**
 * The Jinja expression a Fact stands for. Only the FAQ's structured data
 * uses it, to stay byte-for-byte what the live site serves (main.py parses
 * faq.md before the macros render, so the live JSON-LD carries the raw
 * expression); see src/lib/faq.ts.
 */
export function jinja(path, filters = '') {
  let expr = path;
  const pipes = [];
  for (const name of filters.split(/\s+/).filter(Boolean)) {
    if (name === 'first_word') expr += '.split()[0]';
    else pipes.push(name);
  }
  return `{{ ${[expr, ...pipes].join(' | ')} }}`;
}
