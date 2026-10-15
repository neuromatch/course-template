// Hidden anywidget at the top of each browser page: publishes the cell manifest
// to the page runtime and copies page.css into <head>. Renders nothing.

import { pageRuntime } from './runtime.mjs';

/** Copy the page stylesheet link from the shadow root into <head> (once). */
function installPageStyles(el) {
  const link = el.querySelector('link[rel="stylesheet"]') ?? el.getRootNode().querySelector('link[rel="stylesheet"]');
  if (!link || document.head.querySelector('link[data-nma-cells]')) return;
  const copy = document.createElement('link');
  copy.rel = 'stylesheet';
  copy.href = link.href;
  copy.dataset.nmaCells = '';
  document.head.appendChild(copy);
}

export default {
  render({ model, el }) {
    installPageStyles(el);
    const rt = pageRuntime();
    rt.bundleUrl ||= import.meta.url;
    rt.setCells(model.get('cells'));
  },
};
