// The `nma:` block of the course's myst.yml.
// Twin in Python: nma_kit.config.read_nma_block; fixtures in fixtures/nma_config/.

export function scalar(raw) {
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
