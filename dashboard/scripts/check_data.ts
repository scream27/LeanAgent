import { readFileSync } from 'node:fs';
import { parseSnapshot } from '../src/lib/model.ts';

const root = new URL('../public/data/', import.meta.url);
const files: unknown = JSON.parse(readFileSync(new URL('index.json', root), 'utf8'));
if (!Array.isArray(files) || new Set(files).size !== files.length) {
  throw new Error('data/index.json must be a list of snapshot filenames without duplicates.');
}
for (const file of files) {
  if (typeof file !== 'string' || !/^[a-z0-9-]+\.json$/.test(file) || file === 'index.json') {
    throw new Error(`Invalid snapshot filename: ${String(file)}`);
  }
  const snapshot = parseSnapshot(JSON.parse(readFileSync(new URL(file, root), 'utf8')));
  if (`${snapshot.id}.json` !== file) {
    throw new Error(`Snapshot ID does not match filename: ${file}`);
  }
  console.log(`Validated ${file}: ${snapshot.problems.length} problems`);
}
if (files.length === 0) console.log('No published results.');
