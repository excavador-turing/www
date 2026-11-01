#!/usr/bin/env node
// The security headers of the built site (public/_headers, copied to the build
// output) against the pages they protect. A static `_headers` file cannot compute
// the hash of an inline script, so this check does: every inline script that a
// page runs must have its sha256 in the script-src of the rule that covers the
// page, and every hash in a rule must still be used. A Starlight or Astro upgrade
// that changes an inline script fails here with the line to paste, instead of
// shipping a page whose theme or search script the browser silently refuses to run.
//
// Pages are judged by one of four rules: `/*` (the site) and `/demo/<pane>/*` for each
// of the three demo panes (stock, fork, fleet), which the front page frames and which
// carry the ribbon script of scripts/demo-ribbon.py. /demo/ itself is a page of the
// site; only the panes get their own rule. The stock pane is committed; fork and
// fleet are built by publish.yaml from BMC-UI, so a pane that is not in the build
// is not checked for unused hashes.
//
//   site/scripts/check-csp.mjs [dist]          check (default dist: site/dist)
//   site/scripts/check-csp.mjs [dist] --print  print the sha256 tokens in use, per rule
//
// Also checked, each failing closed (an empty sweep is a failure):
//   - the headers every response must carry are in the `/*` rule;
//   - each pane rule detaches the framing headers of `/*` before setting its own;
//   - no page has an inline event handler or a javascript: URL (the CSP blocks them);
//   - the file stays inside Cloudflare's limits: lines under 2000 characters,
//     fewer than 100 rules;
//   - the file does not set Strict-Transport-Security (the zone does).
import { createHash } from 'node:crypto';
import { existsSync, readdirSync, readFileSync } from 'node:fs';
import { dirname, join, relative, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = join(dirname(fileURLToPath(import.meta.url)), '..', '..');
const args = process.argv.slice(2);
const print = args.includes('--print');
const dist = resolve(root, args.find((a) => !a.startsWith('--')) ?? 'site/dist');

const problems = [];
const bad = (m) => problems.push(m);

// The inline scripts a browser executes. Data blocks are not governed by script-src.
const DATA_TYPES = /^(application\/(ld\+)?json|importmap|speculationrules|text\/(template|html|plain))$/i;
const inlineScripts = (html) => {
  const out = [];
  for (const m of html.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script[^>]*>/gi)) {
    if (/\bsrc\s*=/i.test(m[1])) continue;
    const type = /\btype\s*=\s*"([^"]*)"/i.exec(m[1])?.[1];
    if (type && DATA_TYPES.test(type.trim())) continue;
    out.push(m[2]);
  }
  return out;
};
const sha256 = (s) => `'sha256-${createHash('sha256').update(s, 'utf8').digest('base64')}'`;

const pages = [];
const walk = (dir) => {
  for (const e of readdirSync(dir, { withFileTypes: true })) {
    const f = join(dir, e.name);
    if (e.isDirectory()) walk(f);
    else if (e.name.endsWith('.html')) pages.push(f);
  }
};
walk(dist);
if (pages.length < 10) bad(`only ${pages.length} pages under ${dist}; is this a built site?`);

const PANES = ['stock', 'fork', 'fleet'];
const paneRule = (pane) => `/demo/${pane}/*`;
// rule path -> Map(token -> first page that runs it)
const used = Object.fromEntries(['/*', ...PANES.map(paneRule)].map((r) => [r, new Map()]));
const built = new Set(); // panes with a page in this build
for (const f of pages) {
  const html = readFileSync(f, 'utf8');
  const rel = relative(dist, f).split(sep).join('/');
  const pane = PANES.find((p) => rel.startsWith(`demo/${p}/`));
  if (pane) built.add(pane);
  const rule = pane ? paneRule(pane) : '/*';
  for (const body of inlineScripts(html)) {
    const t = sha256(body);
    if (!used[rule].has(t)) used[rule].set(t, rel);
  }
  if (/<[a-z][^>]*\son[a-z]+\s*=/i.test(html)) bad(`${rel}: an inline event handler; the CSP blocks it. Use addEventListener.`);
  if (/\b(href|src|action)\s*=\s*"\s*javascript:/i.test(html)) bad(`${rel}: a javascript: URL; the CSP blocks it`);
}
if (!used['/*'].size) bad('no inline script found in any page; the sweep checked nothing');
if (!built.has('stock')) bad('no demo/stock page in the build; it is committed under site/public/demo/stock');
const tokens = (rule) => [...used[rule].keys()].sort().join(' ');
if (print) {
  for (const rule of Object.keys(used)) console.log(`${rule}: ${tokens(rule)}`);
  process.exit(0);
}

const file = join(dist, '_headers');
if (!existsSync(file)) {
  console.error(`check-csp: no ${file}; site/public/_headers is missing`);
  process.exit(1);
}
const text = readFileSync(file, 'utf8');
text.split('\n').forEach((l, i) => { if (l.length > 2000) bad(`_headers line ${i + 1} is ${l.length} characters; Cloudflare ignores lines over 2000`); });

// Rules: a path line at column 0, then indented header lines (`Name: value`, or `! Name` to detach).
const sections = new Map();
let cur = null;
for (const line of text.split('\n')) {
  if (!line.trim() || line.trimStart().startsWith('#')) continue;
  if (!/^\s/.test(line)) { cur = line.trim(); sections.set(cur, []); } else if (cur) sections.get(cur).push(line.trim());
}
if (sections.size >= 100) bad(`_headers has ${sections.size} rules; Cloudflare reads fewer than 100`);
const header = (sec, name) => sections.get(sec)?.find((l) => l.toLowerCase().startsWith(name.toLowerCase() + ':'))?.slice(name.length + 1).trim();
const detaches = (sec, name) => sections.get(sec)?.some((l) => l.replace(/^!\s*/, '').toLowerCase() === name.toLowerCase() && l.startsWith('!'));

for (const [sec, lines] of sections) {
  if (lines.some((l) => /^strict-transport-security\s*:/i.test(l))) {
    bad(`the ${sec} rule sets Strict-Transport-Security; the zone sets HSTS and replaces it, so it does not belong here`);
  }
}

const policy = (rule, { framing, checkUnused = true }) => {
  if (!sections.get(rule)) { bad(`_headers has no ${rule} rule`); return; }
  const csp = header(rule, 'Content-Security-Policy') ?? '';
  if (!csp) { bad(`the ${rule} rule sets no Content-Security-Policy`); return; }
  const dir = (n) => csp.split(';').map((d) => d.trim()).find((d) => d.split(/\s+/)[0] === n);
  for (const [n, want] of [['frame-ancestors', framing], ['object-src', "'none'"], ['base-uri', "'self'"], ['default-src', "'self'"]]) {
    if (!dir(n)?.split(/\s+/).slice(1).includes(want)) bad(`the ${rule} CSP lacks ${n} ${want}`);
  }
  const script = dir('script-src') ?? '';
  if (/'unsafe-inline'|'unsafe-eval'|\*/.test(script)) bad(`the ${rule} script-src allows unsafe-inline, unsafe-eval or a wildcard: ${script.slice(0, 80)}`);
  const listed = new Set(script.split(/\s+/).filter((t) => t.startsWith("'sha256-")));
  for (const [t, page] of used[rule]) if (!listed.has(t)) bad(`the ${rule} script-src lacks ${t} (inline script on ${page})`);
  if (checkUnused) for (const t of listed) if (!used[rule].has(t)) bad(`the ${rule} script-src lists ${t}, which no page uses any more; remove it`);
};

if (!sections.get('/*')) bad('_headers has no /* rule');
else {
  for (const h of ['Content-Security-Policy', 'X-Content-Type-Options', 'X-Frame-Options', 'Referrer-Policy', 'Permissions-Policy']) {
    if (!header('/*', h)) bad(`the /* rule sets no ${h}`);
  }
  policy('/*', { framing: "'none'" });
}

// The demo panes are framed by the front page, so they may be framed by this origin and
// no other. Headers of matching rules are merged (a second CSP would be enforced WITH
// the first, a second X-Frame-Options would corrupt it), so the rule detaches the
// site's two before it sets its own.
for (const pane of PANES) {
  const rule = paneRule(pane);
  if (!sections.get(rule)) { bad(`_headers has no ${rule} rule`); continue; }
  if (!detaches(rule, 'Content-Security-Policy')) bad(`the ${rule} rule does not detach the /* Content-Security-Policy; both would be enforced`);
  if (!detaches(rule, 'X-Frame-Options')) bad(`the ${rule} rule does not detach the /* X-Frame-Options (DENY stops the front page framing the pane)`);
  if (header(rule, 'X-Frame-Options')) bad(`the ${rule} rule sets X-Frame-Options; use the CSP's frame-ancestors 'self' alone`);
  policy(rule, { framing: "'self'", checkUnused: built.has(pane) });
}
if (sections.has('/demo/*')) bad('a /demo/* rule would cover the /demo/ page, which is a page of the site; give each pane its own rule');

const assets = sections.get('/_astro/*');
if (!assets) bad('_headers has no /_astro/* rule');
else if (header('/_astro/*', 'Cache-Control') !== 'public, max-age=31536000, immutable') bad('the /_astro/* rule is not Cache-Control: public, max-age=31536000, immutable');
for (const sec of sections.keys()) {
  if (sec !== '/_astro/*' && sections.get(sec).some((l) => /^cache-control\s*:.*immutable/i.test(l))) {
    bad(`${sec} marks responses immutable; only the hashed filenames under /_astro/ may be`);
  }
}

// Every file under /_astro/ must carry its content hash in its name, or immutable would pin stale bytes.
if (existsSync(join(dist, '_astro'))) {
  const unhashed = readdirSync(join(dist, '_astro')).filter((n) => !/[.-][A-Za-z0-9_-]{5,}\.[a-z0-9]+$/.test(n));
  if (unhashed.length) bad(`under /_astro/ but not named by content hash, so not safe to cache forever: ${unhashed.slice(0, 5).join(' ')}`);
} else bad('no _astro directory in the build; the /_astro/* rule covers nothing');

if (problems.length) {
  for (const p of problems) console.error(`check-csp: ${p}`);
  for (const rule of Object.keys(used)) {
    console.error(`check-csp: the sha256 tokens in use for the ${rule} rule, to paste into its script-src in site/public/_headers:\n${tokens(rule)}`);
  }
  process.exit(1);
}
console.log(`check-csp: ok (${pages.length} pages, ${used['/*'].size} site hashes, panes checked: ${[...built].sort().join(' ')})`);
