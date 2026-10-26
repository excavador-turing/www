// /llms.txt, curated: the index scripts/llms.py writes from the nav and each
// page's description -- what turingpi.xyz serves today. Injected by
// astro.config.mjs only when its `llmsTxt` switch says 'curated'; with
// 'plugin', starlight-llms-txt serves /llms.txt (and llms-full/-small) instead.
import type { APIRoute } from 'astro';
import text from '../data/llms.txt?raw';

export const prerender = true;

export const GET: APIRoute = () =>
  new Response(text, { headers: { 'Content-Type': 'text/plain; charset=utf-8' } });
