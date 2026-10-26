// Bold and code, which is all a comparison cell or a board report uses:
// main.py's _md_inline(), escaped first so the text can be nothing but text.
const ESCAPES: Record<string, string> = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#x27;' };

export function escapeHtml(s: string): string {
  return s.replace(/[&<>"']/g, (c) => ESCAPES[c]!);
}

export function inlineMarkdown(s: string): string {
  return escapeHtml(s)
    .replace(/\*\*(.+?)\*\*/g, '<b>$1</b>')
    .replace(/`([^`]+)`/g, '<code>$1</code>');
}
