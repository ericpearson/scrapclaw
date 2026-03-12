import { stat } from 'node:fs/promises';
import { resolve } from 'node:path';

import { readGlobalConfig } from '/Users/epearson/.nvm/versions/node/v25.6.1/lib/node_modules/clawhub/dist/config.js';
import { listTextFiles } from '/Users/epearson/.nvm/versions/node/v25.6.1/lib/node_modules/clawhub/dist/skills.js';

const folderArg = process.argv[2];
if (!folderArg) {
  throw new Error('Usage: node .codex_publish_clawhub.mjs <folder>');
}

const folder = resolve(folderArg);
const folderStat = await stat(folder).catch(() => null);
if (!folderStat?.isDirectory()) {
  throw new Error(`Path must be a folder: ${folder}`);
}

const config = await readGlobalConfig();
if (!config?.token) {
  throw new Error('ClawHub token not found. Run `clawhub login` first.');
}

const filesOnDisk = await listTextFiles(folder);
if (!filesOnDisk.some((file) => file.relPath.toLowerCase() === 'skill.md')) {
  throw new Error('SKILL.md required');
}

const form = new FormData();
form.set(
  'payload',
  JSON.stringify({
    slug: 'scrapclaw',
    displayName: 'Scrapclaw',
    version: '0.0.6',
    changelog: 'Add optional response truncation so callers can cap HTML or text payload size per request.',
    tags: ['latest'],
    acceptLicenseTerms: true,
  }),
);

for (const file of filesOnDisk) {
  const blob = new Blob([Buffer.from(file.bytes)], {
    type: file.contentType ?? 'text/plain',
  });
  form.append('files', blob, file.relPath);
}

const response = await fetch(new URL('/api/v1/skills', config.registry || 'https://clawhub.ai'), {
  method: 'POST',
  headers: {
    Accept: 'application/json',
    Authorization: `Bearer ${config.token}`,
  },
  body: form,
});

const bodyText = await response.text();
if (!response.ok) {
  throw new Error(`HTTP ${response.status}: ${bodyText}`);
}

console.log(bodyText);
