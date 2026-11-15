import { spawnSync } from 'node:child_process';
const python = process.platform === 'win32' ? '.venv/Scripts/python.exe' : '.venv/bin/python';
const result = spawnSync(python, ['-m', 'unittest', 'discover', '-s', 'backend/tests', '-v'], { stdio: 'inherit' });
if (result.status !== 0) process.exit(result.status ?? 1);
const frontend = spawnSync(process.execPath, ['--test', 'app/lib/research-client.test.mjs'], { stdio: 'inherit' });
process.exit(frontend.status ?? 1);
