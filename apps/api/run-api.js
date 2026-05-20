const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

const isWin = process.platform === 'win32';
const pythonBin = isWin ? 'Scripts' : 'bin';
const pythonExe = isWin ? 'python.exe' : 'python';

const localVenv = path.join(__dirname, '.venv', pythonBin, pythonExe);

// Fallback to system python if .venv doesn't exist
const pythonPath = fs.existsSync(localVenv) ? localVenv : pythonExe;

console.log(`Starting API server using Python: ${pythonPath}`);

const uvicorn = spawn(pythonPath, [
  '-m',
  'uvicorn',
  'app.main:app',
  '--host',
  '0.0.0.0',
  '--port',
  '8000',
  '--reload'
], {
  stdio: 'inherit',
  shell: true,
  cwd: __dirname
});

uvicorn.on('close', (code) => {
  process.exit(code);
});
