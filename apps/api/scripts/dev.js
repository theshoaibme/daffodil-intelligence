const { spawn, execSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const http = require('http');

const ROOT = path.resolve(__dirname, '..');
const isWin = process.platform === 'win32';
const PYTHON = isWin 
  ? path.join(ROOT, '.venv', 'Scripts', 'python.exe')
  : path.join(ROOT, '.venv', 'bin', 'python');

if (!fs.existsSync(PYTHON)) {
  console.error(`Missing virtualenv at apps/api/.venv — create it and install deps first.`);
  process.exit(1);
}

const PORT = process.env.API_PORT || '8000';

// Check if port is in use
const server = http.createServer();
server.once('error', (err) => {
  if (err.code === 'EADDRINUSE') {
    // Port is in use, check /health
    checkHealth();
  } else {
    console.error(err);
    process.exit(1);
  }
});

server.once('listening', () => {
  server.close();
  startUvicorn();
});

server.listen(PORT, '0.0.0.0');

function checkHealth() {
  const req = http.get(`http://127.0.0.1:${PORT}/health`, (res) => {
    if (res.statusCode === 200) {
      console.log(`API already running at http://localhost:${PORT} (health OK)`);
      console.log(`Restart: DAFFODIL_API_RESTART=1 pnpm dev`);
      process.exit(0);
    } else {
      handlePortInUseFailure();
    }
  });

  req.on('error', () => {
    handlePortInUseFailure();
  });

  req.end();
}

function handlePortInUseFailure() {
  if (process.env.DAFFODIL_API_RESTART === '1') {
    console.log(`Restarting API on port ${PORT}...`);
    try {
      if (isWin) {
        // Find PID on port using netstat
        const output = execSync(`netstat -ano | findstr :${PORT}`).toString();
        const lines = output.split('\n');
        for (const line of lines) {
          const parts = line.trim().split(/\s+/);
          if (parts.length >= 5 && parts[1].endsWith(`:${PORT}`)) {
            const pid = parts[parts.length - 1];
            if (pid && pid !== '0') {
              execSync(`taskkill /F /PID ${pid}`);
            }
          }
        }
      } else {
        execSync(`fuser -k ${PORT}/tcp`, { stdio: 'ignore' });
      }
    } catch (e) {
      // Ignore errors if killing fails
    }
    // Wait a bit and start
    setTimeout(startUvicorn, 1000);
  } else {
    console.error(`Port ${PORT} is in use but /health failed — another process may own the port.`);
    if (isWin) {
      console.error(`  Please free the port or set DAFFODIL_API_RESTART=1`);
    } else {
      console.error(`  Stop:  fuser -k ${PORT}/tcp`);
      console.error(`  Then:  pnpm dev`);
    }
    process.exit(1);
  }
}

function startUvicorn() {
  const args = [
    '-m', 'uvicorn', 'app.main:app',
    '--host', '0.0.0.0',
    '--port', PORT,
    '--reload',
    '--log-level', 'critical',
    '--no-access-log'
  ];

  const child = spawn(PYTHON, args, {
    stdio: 'inherit',
    cwd: ROOT,
    shell: isWin
  });

  child.on('close', (code) => {
    process.exit(code || 0);
  });
}
