const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

// Desktop Kit install requires OS packages + venv — skip on CI/Vercel (web-only deploys).
if (
  process.env.VERCEL === '1' ||
  process.env.CI === 'true' ||
  process.env.SKIP_DAFFODIL_KIT_INSTALL === '1'
) {
  console.log('[copycat] Skipping Daffodil Kit install (CI/Vercel).');
  process.exit(0);
}

console.log('[copycat] Running post-install hook to install Daffodil Kit...');

// Determine root directory (assuming structure is apps/copycat/postinstall.js)
const rootDir = path.resolve(__dirname, '../..');
const isWindows = process.platform === 'win32';

let cmd = '';
let args = [];

if (isWindows) {
  const psScript = path.join(rootDir, 'packages/daffodil-kit/install.ps1');
  if (fs.existsSync(psScript)) {
    cmd = 'powershell.exe';
    args = ['-ExecutionPolicy', 'Bypass', '-File', psScript];
  } else {
    console.log('[copycat] install.ps1 not found locally, fetching from GitHub...');
    cmd = 'powershell.exe';
    args = ['-Command', 'irm https://raw.githubusercontent.com/the-shoaib2/daffodil-intelligence/main/install.ps1 | iex'];
  }
} else {
  const shScript = path.join(rootDir, 'install');
  if (fs.existsSync(shScript)) {
    cmd = 'sh';
    args = [shScript];
  } else {
    console.log('[copycat] install script not found locally, fetching from GitHub...');
    cmd = 'sh';
    args = ['-c', 'curl -fsSL https://raw.githubusercontent.com/the-shoaib2/daffodil-intelligence/main/install | sh'];
  }
}

console.log(`[copycat] Executing: ${cmd} ${args.join(' ')}`);

// Set DAFFODIL_KIT_USE_LOCAL=1 to use the local codebase if running locally
const env = { ...process.env };
const localKitPath = path.join(rootDir, 'packages/daffodil-kit');
if (fs.existsSync(localKitPath)) {
  env.DAFFODIL_KIT_USE_LOCAL = '1';
}

const proc = spawn(cmd, args, {
  cwd: rootDir,
  stdio: 'inherit',
  shell: true,
  env
});

proc.on('close', (code) => {
  if (code !== 0) {
    console.error(`[copycat] Daffodil Kit installation failed with code ${code}`);
    process.exit(code);
  }
  console.log('[copycat] Daffodil Kit installed successfully.');
});
