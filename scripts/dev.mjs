import { spawn } from 'node:child_process';
import { existsSync } from 'node:fs';
const python = process.platform === 'win32' ? '.venv/Scripts/python.exe' : '.venv/bin/python';
if (!existsSync(python)) { console.error('Create the project environment first: python -m venv .venv'); process.exit(1); }
const children = [
  spawn(python, ['-m', 'uvicorn', 'backend.main:app', '--host', '127.0.0.1', '--port', '8000', '--no-access-log'], { stdio: 'inherit' }),
  spawn(process.execPath, ['node_modules/next/dist/bin/next', 'dev', '--hostname', '127.0.0.1'], { stdio: 'inherit', env: { ...process.env, NEXT_TELEMETRY_DISABLED: '1' } })
];
let stopping = false;
function stop(code = 0) { if (stopping) return; stopping = true; for (const child of children) child.kill(); process.exitCode = code; }
process.on('SIGINT', () => stop());
process.on('SIGTERM', () => stop());
for (const child of children) { child.on('error', () => stop(1)); child.on('exit', code => stop(code || 0)); }
