import { readFile } from 'node:fs/promises';
import { setTimeout } from 'node:timers/promises';

const base = 'https://lean-arena-dashboard.vercel.app';
const index = await readFile(new URL('../public/data/index.json', import.meta.url), 'utf8');
const files = JSON.parse(index);
if (!Array.isArray(files) || !files.length || files.some(f => !/^[a-z0-9-]+\.json$/.test(f))) {
  throw new Error('Invalid local snapshot index');
}
const expected = new Map([['index.json', index]]);
for (const file of files) {
  expected.set(file, await readFile(new URL(`../public/data/${file}`, import.meta.url), 'utf8'));
}

for (let attempt = 1; attempt <= 12; attempt++) {
  try {
    for (const [file, body] of expected) {
      const response = await fetch(`${base}/data/${file}?deployment-check=${Date.now()}`, {
        cache: 'no-store', signal: AbortSignal.timeout(10000),
      });
      if (!response.ok) throw new Error(`${file}: HTTP ${response.status}`);
      if ((await response.text()) !== body) throw new Error(`${file}: production differs from the tested source`);
    }
    console.log(`Production data matches ${files.length} tested snapshot(s): ${base}`);
    break;
  } catch (error) {
    if (attempt === 12) throw error;
    console.log(`Waiting for production update (${attempt}/12): ${error.message}`);
    await setTimeout(5000);
  }
}
