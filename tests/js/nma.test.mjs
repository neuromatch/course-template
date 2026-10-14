// Run with: node --test tests/js/*.test.mjs
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, readdirSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

import { readNmaConfig, pagePrefix, defaultPrefix } from '../../plugins/nma.mjs';
import { send, timestamp } from '../../plugins/nma-feedback.mjs';

const here = dirname(fileURLToPath(import.meta.url));
const fixtures = join(here, '..', 'fixtures', 'nma_config');

// The same fixtures are checked against PyYAML in tests/test_nma_feedback.py.
for (const name of readdirSync(fixtures).filter((f) => f.endsWith('.yml'))) {
  test(`readNmaConfig matches ${name}`, () => {
    const text = readFileSync(join(fixtures, name), 'utf8');
    const expected = JSON.parse(readFileSync(join(fixtures, name.replace(/\.yml$/, '.json')), 'utf8'));
    assert.deepEqual(readNmaConfig(text), expected);
  });
}

test('the real myst.yml has complete feedback settings', () => {
  const text = readFileSync(join(here, '..', '..', 'myst.yml'), 'utf8');
  const { feedback } = readNmaConfig(text);
  for (const key of ['url', 'project', 'user_key']) assert.ok(feedback?.[key], key);
});

test('prefix from frontmatter, else from the filename', () => {
  assert.equal(pagePrefix('---\ntitle: T\nfeedback_prefix: W2D2_T1\n---\n', 'W2D1_Tutorial1'), 'W2D2_T1');
  assert.equal(pagePrefix("---\nfeedback_prefix: 'W2D2_T1'  # legacy\n---\n", 'x'), 'W2D2_T1');
  assert.equal(pagePrefix('---\ntitle: T\n---\n', 'W2D1_Tutorial1'), 'W2D1_T1');
  assert.equal(pagePrefix('body\nfeedback_prefix: X\n', 'W10D3_Tutorial12'), 'W10D3_T12');
  assert.equal(defaultPrefix('W1D2_Bonus'), 'W1D2_Bonus');
});

test('timestamp matches vibecheck (no trailing Z)', () => {
  assert.equal(timestamp(new Date(Date.UTC(2026, 9, 13, 1, 2, 3, 4))), '2026-10-13T01:02:03.004');
});

const settings = { section_id: 'W2D2_T1_Video', url: 'https://e.org/klab/', project: 'neuromatch_cn', user_key: 'k' };
const reply = (body, ok = true) => async () => ({ ok, json: async () => body });

test('send posts the vibecheck payload', async () => {
  let call;
  const fetchImpl = async (url, init) => {
    call = { url, init };
    return { ok: true, json: async () => ({ status: 'success' }) };
  };
  assert.equal(await send(settings, 'sad', 'too fast', fetchImpl), true);
  assert.equal(call.url, 'https://e.org/klab/api/v1/projects/neuromatch_cn');
  assert.equal(call.init.method, 'POST');
  assert.deepEqual(call.init.headers, { 'Content-Type': 'application/json', 'X-User-Key': 'k' });
  const body = JSON.parse(call.init.body);
  assert.deepEqual(Object.keys(body), ['button_name', 'feedback', 'section_id', 'timestamp_utc']);
  assert.equal(body.button_name, 'sad');
  assert.equal(body.feedback, 'too fast');
  assert.equal(body.section_id, 'W2D2_T1_Video');
});

test('send reports failures', async () => {
  assert.equal(await send(settings, 'happy', '', reply({ status: 'error', message: 'x' })), false);
  assert.equal(await send(settings, 'happy', '', reply({}, false)), false);
  assert.equal(await send(settings, 'happy', '', async () => { throw new TypeError('offline'); }), false);
});
