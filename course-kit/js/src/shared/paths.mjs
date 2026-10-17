// Where a course page and its generated files live.
// Twins in Python: nma_kit.config (page_location) and nma_kit.convert
// (make_badge_html); shared fixtures in fixtures/config/.

import { readFileSync } from 'node:fs';
import { join, relative, sep } from 'node:path';

export const NOTEBOOKS_BRANCH = 'notebooks-branch';

let cachedRepo;
export function githubRepo() {
  if (cachedRepo === undefined) {
    let config = '';
    try {
      config = readFileSync(join(process.cwd(), 'myst.yml'), 'utf8');
    } catch {
      // handled below
    }
    const match = config.match(/^\s*github:\s*['"]?https?:\/\/github\.com\/([^\s'"]+?)\/?['"]?\s*$/m);
    cachedRepo = match ? match[1] : null;
  }
  return cachedRepo;
}

// tutorials/W2D1_Examples/W2D1_Tutorial1.md -> { relDir: 'W2D1_Examples', stem: 'W2D1_Tutorial1' }
export function pageLocation(filePath) {
  const rel = relative(process.cwd(), filePath).split(sep).join('/');
  if (!rel.startsWith('tutorials/')) return null;
  const parts = rel.slice('tutorials/'.length).split('/');
  const stem = parts.pop().replace(/\.[^.]+$/, '');
  return { relDir: parts.join('/'), stem };
}

/** Colab and Kaggle URLs of a page's generated notebook (same as make_badge_html in convert_to_notebooks.py). */
export function notebookUrls(filePath) {
  const repo = githubRepo();
  const location = pageLocation(filePath);
  if (!repo || !location) return { colabUrl: 'https://colab.research.google.com/', kaggleUrl: 'https://www.kaggle.com/' };
  const path = ['notebooks', location.relDir, `${location.stem}.ipynb`].filter(Boolean).join('/');
  return {
    colabUrl: `https://colab.research.google.com/github/${repo}/blob/${NOTEBOOKS_BRANCH}/${path}`,
    kaggleUrl: `https://kaggle.com/kernels/welcome?src=https://raw.githubusercontent.com/${repo}/${NOTEBOOKS_BRANCH}/${path}`,
  };
}
