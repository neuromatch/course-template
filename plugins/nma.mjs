// Renders {nma-video} and {nma-slides} as static embeds on the website.
// scripts/nma_media.py builds the matching notebook code cells.
// Keep the URL templates in both files in sync.
//
// Also renders {nma-solution} / {nma-explanation} as links (see
// scripts/nma_solutions.py) and {nma-feedback} as a feedback widget (see
// plugins/nma-feedback.mjs and scripts/nma_feedback.py).

import { readFileSync } from 'node:fs';
import { join, relative, sep } from 'node:path';

const VIDEO_SOURCES = [
  {
    option: 'youtube',
    label: 'YouTube',
    embed: (id) => `https://www.youtube.com/embed/${id}?rel=0`,
    page: (id) => `https://youtube.com/watch?v=${id}`,
  },
  {
    option: 'bilibili',
    label: 'Bilibili',
    embed: (id) => `https://player.bilibili.com/player.html?bvid=${id}&page=1&autoplay=0`,
    page: (id) => `https://www.bilibili.com/video/${id}`,
  },
  {
    option: 'osf',
    label: 'OSF',
    embed: (id) =>
      `https://mfr.ca-1.osf.io/render?url=https://osf.io/download/${id}/?direct%26mode=render`,
    page: (id) => `https://osf.io/${id}`,
  },
];

const text = (value) => ({ type: 'text', value });
const link = (url, label) => ({ type: 'link', url, children: [text(label ?? url)] });
const iframe = (src, title) => ({ type: 'iframe', src, width: '100%', title });
const heading = (title) => ({
  type: 'paragraph',
  children: [{ type: 'strong', children: [text(title)] }],
});

function fail(vfile, node, message) {
  const msg = vfile.message(message, node, 'nma-plugin');
  msg.fatal = true;
  return [];
}

const nmaVideo = {
  name: 'nma-video',
  doc: 'Lecture video with one tab per host (YouTube, Bilibili, OSF).',
  arg: { type: String, required: true, doc: 'Video title, e.g. "Video 1: Intro".' },
  options: {
    youtube: { type: String, doc: 'YouTube video id.' },
    bilibili: { type: String, doc: 'Bilibili BV id.' },
    osf: { type: String, doc: 'OSF file id.' },
  },
  run(data, vfile) {
    const sources = VIDEO_SOURCES.filter((s) => data.options?.[s.option]).map((s) => ({
      ...s,
      id: data.options[s.option],
    }));
    if (sources.length === 0) {
      return fail(vfile, data.node, 'nma-video needs at least one of :youtube:, :bilibili:, :osf:');
    }
    const player =
      sources.length === 1
        ? iframe(sources[0].embed(sources[0].id), data.arg)
        : {
            type: 'tabSet',
            children: sources.map((s) => ({
              type: 'tabItem',
              title: s.label,
              children: [iframe(s.embed(s.id), `${data.arg} (${s.label})`)],
            })),
          };
    const links = sources.map((s) => ({
      type: 'paragraph',
      children: [text('Video available at '), link(s.page(s.id))],
    }));
    return [{ type: 'div', class: 'nma-video', children: [heading(data.arg), player, ...links] }];
  },
};

const nmaSlides = {
  name: 'nma-slides',
  doc: 'Embedded OSF slide deck with a download link.',
  arg: { type: String, required: true, doc: 'OSF file id, e.g. snv4m.' },
  options: { title: { type: String, doc: 'Heading shown above the slides.' } },
  run(data) {
    const id = data.arg;
    const title = data.options?.title ?? 'Tutorial slides';
    const src = `https://mfr.ca-1.osf.io/render?url=https://osf.io/${id}/?direct%26mode=render%26action=download%26mode=render`;
    return [
      {
        type: 'div',
        class: 'nma-slides',
        children: [
          heading(title),
          iframe(src, title),
          {
            type: 'paragraph',
            children: [link(`https://osf.io/download/${id}/`, 'Download the slides')],
          },
        ],
      },
    ];
  },
};

// ---------------------------------------------------------------------------
// {nma-solution} / {nma-explanation}: render as a "Click for ..." link to the
// solution file that scripts/nma_solutions.py writes to notebooks-branch.
// The solution text itself is never put on the page.
//
// The directives only emit a placeholder. The transform below numbers the
// placeholders in document order and builds the links. The file naming and URL
// rules must stay in sync with scripts/nma_solutions.py.

const SOLUTION_KINDS = {
  'nma-solution': { label: 'Click for solution', file: (stem, n) => `${stem}_Solution_${n}.py` },
  'nma-explanation': {
    label: 'Click for explanation',
    file: (stem, n) => `${stem}_Explanation_${n}.md`,
  },
};
const NOTEBOOKS_BRANCH = 'notebooks-branch';
const PLACEHOLDER = 'nmaSolutionRef';

const solutionDirective = (name, doc) => ({
  name,
  doc,
  body: { type: String, required: true, doc: 'Hidden on the site; see scripts/nma_solutions.py.' },
  run(data) {
    return [{ type: PLACEHOLDER, kind: name, position: data.node.position }];
  },
});

let cachedRepo;
function githubRepo() {
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
function pageLocation(filePath) {
  const rel = relative(process.cwd(), filePath).split(sep).join('/');
  if (!rel.startsWith('tutorials/')) return null;
  const parts = rel.slice('tutorials/'.length).split('/');
  const stem = parts.pop().replace(/\.[^.]+$/, '');
  return { relDir: parts.join('/'), stem };
}

function solutionUrl(repo, relDir, filename) {
  const path = ['notebooks', relDir, 'solutions', filename].filter(Boolean).join('/');
  return `https://github.com/${repo}/blob/${NOTEBOOKS_BRANCH}/${path}`;
}

// [node, is top level] for every node of `type`, in document order.
function findPlaceholders(tree, type) {
  const found = [];
  const walk = (node, ancestors) => {
    (node.children ?? []).forEach((child) => {
      if (child.type === type) {
        found.push([child, ancestors.every((a) => a.type === 'root' || a.type === 'block')]);
      } else {
        walk(child, [...ancestors, child]);
      }
    });
  };
  walk(tree, [tree]);
  return found;
}

// Replace a node in place (transforms only get the tree, not parents).
function replaceNode(node, replacement) {
  for (const key of Object.keys(node)) delete node[key];
  Object.assign(node, replacement);
}

const solutionLinks = {
  name: 'nma-solution-links',
  doc: 'Turn nma-solution/nma-explanation placeholders into links to the solution files.',
  stage: 'document',
  plugin: () => (tree, vfile) => {
    const found = findPlaceholders(tree, PLACEHOLDER);
    if (found.length === 0) return;

    const repo = githubRepo();
    const location = pageLocation(vfile.path);
    const counters = {};
    for (const [node, topLevel] of found) {
      const replaceWith = (children, extra = {}) =>
        replaceNode(node, { type: 'div', children, ...extra });
      const kind = node.kind;
      const fatal = (message) => {
        const msg = vfile.message(message, node, 'nma-plugin');
        msg.fatal = true;
        replaceWith([]);
      };
      if (!topLevel) {
        fatal(`${kind} must be at the top level of the page, not inside another directive`);
        continue;
      }
      if (!repo) {
        fatal(`${kind} needs project.github (a github.com URL) in myst.yml`);
        continue;
      }
      if (!location) {
        fatal(`${kind} is only supported in pages under tutorials/`);
        continue;
      }
      counters[kind] = (counters[kind] ?? 0) + 1;
      const { label, file } = SOLUTION_KINDS[kind];
      const url = solutionUrl(repo, location.relDir, file(location.stem, counters[kind]));
      replaceWith(
        [
          {
            type: 'paragraph',
            children: [{ type: 'link', url, children: [{ type: 'emphasis', children: [text(label)] }] }],
          },
        ],
        { class: 'nma-solution-link' },
      );
    }
  },
};

// ---------------------------------------------------------------------------
// {nma-feedback}: a 🙂/😐/🙁 widget that posts to datatops from the browser
// (plugins/nma-feedback.mjs, rendered through MyST's anywidget node, so no
// kernel is needed). scripts/nma_feedback.py builds the matching notebook cells.
//
// Settings come from the top-level `nma:` block in myst.yml:
//
//   nma:
//     feedback:
//       url: https://...
//       project: neuromatch_cn
//       user_key: ...
//
// Plugins can't import a YAML library, so readNmaConfig() understands only
// plain `key: value` lines. read_nma_block() in scripts/nma_feedback.py is
// the Python copy; CI rejects `nma:` blocks the two would read differently.

const FEEDBACK_PLACEHOLDER = 'nmaFeedbackRef';
const FEEDBACK_ESM = '/plugins/nma-feedback.mjs';
const NAME_RE = /^[A-Za-z0-9_]+$/;
const FEEDBACK_KEYS = ['url', 'project', 'user_key'];

function scalar(raw) {
  raw = raw.trim();
  if (!raw || raw.startsWith('#')) return null;
  if (raw[0] === '"' || raw[0] === "'") {
    const end = raw.indexOf(raw[0], 1);
    return end === -1 ? raw : raw.slice(1, end);
  }
  return raw.replace(/\s+#.*$/, '');
}

/** Read the top-level `nma:` block of myst.yml as {section: {key: value}}. */
export function readNmaConfig(text) {
  const out = {};
  let section = null;
  let sectionIndent = null;
  let inside = false;
  for (const line of text.split(/\r?\n/)) {
    if (!inside) {
      inside = /^nma:\s*(#.*)?$/.test(line);
      continue;
    }
    const stripped = line.trim();
    if (!stripped || stripped.startsWith('#')) continue;
    if (!/^\s/.test(line)) break;
    const match = line.match(/^( +)([A-Za-z_][\w-]*):(?:\s+(.*?))?\s*$/);
    if (!match) continue;
    const indent = match[1].length;
    const value = scalar(match[3] ?? '');
    if (value === null) {
      if (sectionIndent === null || indent <= sectionIndent) {
        section = match[2];
        sectionIndent = indent;
        out[section] = {};
      }
    } else if (section !== null && indent > sectionIndent) {
      out[section][match[2]] = value;
    }
  }
  return out;
}

let cachedFeedbackConfig;
function feedbackConfig() {
  if (cachedFeedbackConfig === undefined) {
    let text = '';
    try {
      text = readFileSync(join(process.cwd(), 'myst.yml'), 'utf8');
    } catch {
      // handled by the caller
    }
    const config = readNmaConfig(text).feedback ?? {};
    cachedFeedbackConfig = FEEDBACK_KEYS.every((k) => config[k]) ? config : null;
  }
  return cachedFeedbackConfig;
}

/** W2D1_Tutorial1 -> W2D1_T1; anything else is used as is. */
export function defaultPrefix(stem) {
  const match = stem.match(/^(W\d+D\d+)_Tutorial(\d+)$/);
  return match ? `${match[1]}_T${match[2]}` : stem;
}

/** `feedback_prefix` from the page frontmatter, else derived from the filename. */
export function pagePrefix(text, stem) {
  if (text.startsWith('---')) {
    const end = text.indexOf('\n---', 3);
    const frontmatter = end === -1 ? '' : text.slice(3, end);
    const match = frontmatter.match(/^feedback_prefix:\s*(.*?)\s*$/m);
    const value = match ? scalar(match[1]) : null;
    if (value !== null) return value;
  }
  return defaultPrefix(stem);
}

const nmaFeedback = {
  name: 'nma-feedback',
  doc: 'Feedback widget (🙂/😐/🙁) for one section; posts to datatops.',
  arg: { type: String, required: true, doc: 'Section name, e.g. Linear_Dynamical_Systems_Video.' },
  run(data) {
    return [{ type: FEEDBACK_PLACEHOLDER, section: data.arg ?? '', position: data.node.position }];
  },
};

const feedbackWidgets = {
  name: 'nma-feedback-widgets',
  doc: 'Turn nma-feedback placeholders into anywidget nodes with the datatops settings.',
  stage: 'document',
  plugin: () => (tree, vfile) => {
    const found = findPlaceholders(tree, FEEDBACK_PLACEHOLDER);
    if (found.length === 0) return;

    const config = feedbackConfig();
    let source = '';
    try {
      source = readFileSync(vfile.path, 'utf8');
    } catch {
      // no frontmatter prefix then
    }
    const stem = (vfile.path ?? '').split(/[\\/]/).pop().replace(/\.[^.]+$/, '');
    const prefix = pagePrefix(source, stem);
    const seen = new Set();

    found.forEach(([node, topLevel], n) => {
      const fatal = (message) => {
        const msg = vfile.message(message, node, 'nma-plugin');
        msg.fatal = true;
        replaceNode(node, { type: 'div', children: [] });
      };
      const section = node.section;
      if (!topLevel) return fatal('nma-feedback must be at the top level of the page, not inside another directive');
      if (!NAME_RE.test(section)) {
        return fatal(`nma-feedback section name must use only letters, digits and underscores (got "${section}")`);
      }
      if (seen.has(section)) return fatal(`nma-feedback section ${section} is used twice on this page`);
      seen.add(section);
      if (!NAME_RE.test(prefix)) {
        return fatal(`feedback_prefix must use only letters, digits and underscores (got "${prefix}")`);
      }
      if (!config) return fatal('nma-feedback needs nma.feedback.{url,project,user_key} in myst.yml');
      replaceNode(node, {
        type: 'anywidget',
        esm: FEEDBACK_ESM,
        model: {
          section_id: `${prefix}_${section}`,
          url: config.url,
          project: config.project,
          user_key: config.user_key,
        },
        class: 'nma-feedback',
        id: `nma-feedback-${n + 1}`,
      });
    });
  },
};

export default {
  name: 'Neuromatch media, solutions and feedback',
  directives: [
    nmaVideo,
    nmaSlides,
    solutionDirective('nma-solution', 'Exercise solution, shown as a link to the solution file.'),
    solutionDirective('nma-explanation', 'Discussion answer, shown as a link to the explanation file.'),
    nmaFeedback,
  ],
  transforms: [solutionLinks, feedbackWidgets],
};
