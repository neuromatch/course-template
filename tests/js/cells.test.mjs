// Run with: node --test tests/js/*.test.mjs
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

import {
  NO_FALLBACK_MARKER, isExercise, withNoFallback, modeOf, runtimeOf, thebeId, thebeScriptUrls, statusText,
} from '../../plugins/cells/src/model.mjs';

const here = dirname(fileURLToPath(import.meta.url));
const fixtures = join(here, '..', 'fixtures', 'cells');

// The same fixture is checked in tests/test_nma_cells.py.
for (const c of JSON.parse(readFileSync(join(fixtures, 'runtime.json'), 'utf8'))) {
  test(`runtimeOf: ${c.name}`, () => assert.equal(runtimeOf(c.text), c.runtime));
}

test('modeOf', () => {
  assert.equal(modeOf([]), 'edit');
  assert.equal(modeOf(['remove-cell']), 'hidden');
  assert.equal(modeOf(['remove-input']), 'output');
  assert.equal(modeOf(['hide-input']), 'collapsed');
  assert.equal(modeOf(['hide-cell']), 'collapsed');
  assert.equal(modeOf(['remove-cell', 'hide-input']), 'hidden');
});

test('isExercise', () => {
  assert.ok(isExercise('def f():\n    raise NotImplementedError("x")'));
  assert.ok(!isExercise('# raise NotImplementedError'));
  assert.ok(!isExercise('x = 1'));
});

test('withNoFallback appends the marker once', () => {
  assert.equal(NO_FALLBACK_MARKER, 'nma-no-fallback');
  assert.equal(withNoFallback('x = 1\n\n'), 'x = 1\n# nma-no-fallback\n');
  assert.equal(withNoFallback(withNoFallback('x = 1\n\n')), 'x = 1\n# nma-no-fallback\n');
});

test('thebeId', () => assert.equal(thebeId(7), 'nma-cell-7'));

test('thebeScriptUrls resolves relative to the bundle', () => {
  assert.deepEqual(thebeScriptUrls('https://org.github.io/repo/build/panel-abc.mjs'), {
    core: 'https://org.github.io/repo/thebe-core.min.js',
    lite: 'https://org.github.io/repo/thebe-lite.min.js',
  });
  assert.equal(thebeScriptUrls('https://x.org/build/p.mjs').core, 'https://x.org/thebe-core.min.js');
});

test('statusText', () => {
  assert.equal(statusText({ state: 'running' }), 'Running…');
  assert.equal(statusText({ state: 'done', count: 3 }), '[3] ✓');
  assert.equal(statusText({ state: 'error', count: 4, error: { ename: 'NotImplementedError' } }), '[4] ✗ NotImplementedError');
  assert.equal(statusText({ state: 'error', count: null, error: { ename: 'X' } }), '[ ] ✗ X');
});
