import { describe, it, expect } from 'vitest';
import { existsSync, readFileSync, readdirSync, statSync } from 'node:fs';
import { join, resolve } from 'node:path';

const REPO_ROOT = resolve(__dirname, '..');
const ORPHAN_STUBS = ['test_badge_logic.py', 'test_single_word.py'];

/**
 * Regression tests for TICKET-005 — orphan root-level test stubs removal.
 *
 * The stubs `test_badge_logic.py` and `test_single_word.py` were manual
 * integration scripts (not pytest tests) that lived at the repo root,
 * were never collected by `pytest tests/`, and inflated the apparent test
 * count. These tests guard against the stubs being re-introduced and
 * against source code (Python/JS) importing or referencing them by name.
 */

function walkSourceFiles(dir, acc = []) {
  const skipDirs = new Set([
    'node_modules',
    '.git',
    '.pytest_cache',
    '__pycache__',
    '.claude',
    'api/performance_logs',
    'tests', // don't scan our own test file
  ]);
  for (const entry of readdirSync(dir)) {
    const full = join(dir, entry);
    const rel = full.slice(REPO_ROOT.length + 1);
    if (skipDirs.has(entry) || skipDirs.has(rel)) continue;
    const st = statSync(full);
    if (st.isDirectory()) {
      walkSourceFiles(full, acc);
    } else if (/\.(py|js|ts|mjs|cjs|json|ini|toml|cfg)$/.test(entry)) {
      acc.push(full);
    }
  }
  return acc;
}

describe('TICKET-005: orphan root-level test stubs are removed', () => {
  it.each(ORPHAN_STUBS)('%s does not exist at repo root', (name) => {
    expect(existsSync(join(REPO_ROOT, name))).toBe(false);
  });

  it('no source file imports or references the removed stubs by name', () => {
    const files = walkSourceFiles(REPO_ROOT);
    const offenders = [];
    for (const file of files) {
      const text = readFileSync(file, 'utf8');
      for (const stub of ORPHAN_STUBS) {
        const base = stub.replace(/\.py$/, '');
        // Catch `python test_badge_logic.py`, `import test_single_word`,
        // `from test_badge_logic import ...`, CI entries, etc.
        const patterns = [
          new RegExp(`\\bimport\\s+${base}\\b`),
          new RegExp(`\\bfrom\\s+${base}\\s+import\\b`),
          new RegExp(`\\b${stub.replace('.', '\\.')}\\b`),
        ];
        if (patterns.some((p) => p.test(text))) {
          offenders.push(`${file.slice(REPO_ROOT.length + 1)} references ${stub}`);
        }
      }
    }
    expect(offenders).toEqual([]);
  });

  it('no pytest config (pytest.ini / pyproject.toml) lists the removed stubs in testpaths', () => {
    const configs = ['pytest.ini', 'pyproject.toml', 'setup.cfg', 'tox.ini'];
    for (const cfg of configs) {
      const p = join(REPO_ROOT, cfg);
      if (!existsSync(p)) continue;
      const text = readFileSync(p, 'utf8');
      for (const stub of ORPHAN_STUBS) {
        expect(
          text.includes(stub),
          `${cfg} still references ${stub}`,
        ).toBe(false);
      }
    }
  });
});
