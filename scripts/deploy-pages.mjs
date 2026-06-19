import { copyFileSync, mkdirSync, readdirSync, rmSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const repoRoot = fileURLToPath(new URL('..', import.meta.url));
const outputDir = path.join(repoRoot, '.pages-dist');
const dryRun = process.argv.includes('--dry-run');

rmSync(outputDir, { recursive: true, force: true });
mkdirSync(outputDir, { recursive: true });

for (const filename of ['index.html', '_headers']) {
  copyFileSync(path.join(repoRoot, filename), path.join(outputDir, filename));
}

if (dryRun) {
  console.log(`Pages files: ${readdirSync(outputDir).sort().join(', ')}`);
  process.exit(0);
}

const executable = process.platform === 'win32' ? 'npx.cmd' : 'npx';
const result = spawnSync(
  executable,
  [
    'wrangler',
    'pages',
    'deploy',
    outputDir,
    '--project-name=haorio-itpeflash',
    '--branch=main',
    '--commit-dirty=true',
  ],
  { cwd: repoRoot, stdio: 'inherit' },
);

if (result.error) throw result.error;
process.exit(result.status ?? 1);
