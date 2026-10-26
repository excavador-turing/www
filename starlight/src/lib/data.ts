// The site's data files, for the components that render them.
//
// src/data/ holds what the generators write: facts.yaml (scripts/facts.py),
// boards.yaml (by hand), news-posts.json (scripts/refresh-changelog.py).
// Imported as raw text through Vite, so a changed file is part of
// the build's own dependency graph: the hourly refresh rebuilds with the new
// numbers and no Python runs at render time.
import { parse } from 'yaml';
import { parseFacts } from './facts.mjs';
import factsText from '../data/facts.yaml?raw';
import boardsText from '../data/boards.yaml?raw';
import newsPostsText from '../data/news-posts.json?raw';

export const facts: Record<string, unknown> = parseFacts(factsText);

export type BoardReport = {
  revision?: string;
  firmware?: string;
  date?: string;
  how?: string;
  outcome?: string;
  source?: string;
};

export const boardReports: BoardReport[] = parse(boardsText) ?? [];

/** firmware version -> the slug of the post that announced it. */
export const newsPosts: Record<string, string> = JSON.parse(newsPostsText);
