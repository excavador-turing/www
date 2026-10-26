import type { APIRoute, GetStaticPaths } from 'astro';

// /data/<file>: the site's data, served as it always has been -- facts.yaml
// and roadmap.json among them -- from src/data/, where the generators write
// it and the components read it. One copy, so the two cannot disagree.
// llms.txt is not data: /llms.txt serves it (src/routes/llms.txt.ts).
const files = import.meta.glob('../../data/*', { query: '?raw', import: 'default', eager: true });

const TYPES: Record<string, string> = {
  json: 'application/json',
  yaml: 'application/yaml',
};

export const getStaticPaths = (() =>
  Object.entries(files)
    .map(([path, body]) => ({ file: path.split('/').pop() as string, body: body as string }))
    .filter(({ file }) => file !== 'llms.txt')
    .map(({ file, body }) => ({ params: { file }, props: { body } }))) satisfies GetStaticPaths;

export const GET: APIRoute = ({ params, props }) =>
  new Response(props.body as string, {
    headers: { 'Content-Type': TYPES[String(params.file).split('.').pop() ?? ''] ?? 'text/plain' },
  });
