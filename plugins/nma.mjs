// Renders {nma-video} and {nma-slides} as static embeds on the website.
// scripts/nma_media.py builds the matching notebook code cells.
// Keep the URL templates in both files in sync.
//
// Also renders {nma-solution} / {nma-explanation} as links (see the second
// half of this file and scripts/nma_solutions.py).

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

const solutionLinks = {
  name: 'nma-solution-links',
  doc: 'Turn nma-solution/nma-explanation placeholders into links to the solution files.',
  stage: 'document',
  plugin: () => (tree, vfile) => {
    const found = []; // [placeholder node, is top level]
    const walk = (node, ancestors) => {
      (node.children ?? []).forEach((child) => {
        if (child.type === PLACEHOLDER) {
          found.push([child, ancestors.every((a) => a.type === 'root' || a.type === 'block')]);
        } else {
          walk(child, [...ancestors, child]);
        }
      });
    };
    walk(tree, [tree]);
    if (found.length === 0) return;

    const repo = githubRepo();
    const location = pageLocation(vfile.path);
    const counters = {};
    for (const [node, topLevel] of found) {
      const replaceWith = (children, extra = {}) => {
        for (const key of Object.keys(node)) delete node[key];
        Object.assign(node, { type: 'div', children, ...extra });
      };
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

export default {
  name: 'Neuromatch media and solutions',
  directives: [
    nmaVideo,
    nmaSlides,
    solutionDirective('nma-solution', 'Exercise solution, shown as a link to the solution file.'),
    solutionDirective('nma-explanation', 'Discussion answer, shown as a link to the explanation file.'),
  ],
  transforms: [solutionLinks],
};
