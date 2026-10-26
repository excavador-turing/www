// The upstream-vs-fork rows of reference/comparison: a labelled table row,
// skipping the header rule, the `route` header and the two-catalogue table's
// linked rows. The same parse as main.py's comparison_rows() and
// scripts/facts.py, which counts them into facts.yaml (platform.rows).
export function comparisonRows(markdown: string): [string, string, string][] {
  const rows: [string, string, string][] = [];
  for (const m of markdown.matchAll(/^\|\s*([^|]+?)\s*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|/gm)) {
    const label = m[1]!.trim();
    if (!label || /^[-: ]+$/.test(label) || label.toLowerCase() === 'route') continue;
    if (label.startsWith('[')) continue;
    rows.push([label, m[2]!.trim(), m[3]!.trim()]);
  }
  return rows;
}
