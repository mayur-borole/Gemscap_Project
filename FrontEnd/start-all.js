/**
 * Start script that launches both backend and frontend
 * Backend must start first, then frontend
 */

import { spawn } from 'child_process';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Colors for console output
const colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  green: '\x1b[32m',
  blue: '\x1b[34m',
  yellow: '\x1b[33m',
};

console.log(`${colors.bright}${colors.blue}🚀 Starting GEMSCAP Application...${colors.reset}\n`);

// Start Backend (Python FastAPI)
console.log(`${colors.green}[Backend]${colors.reset} Starting Python server...`);
const backendPath = join(__dirname, '..', 'BackEnd');
const backend = spawn('python', ['run.py'], {
  cwd: backendPath,
  shell: true,
  stdio: 'inherit',
});

backend.on('error', (err) => {
  console.error(`${colors.yellow}[Backend Error]${colors.reset}`, err);
  process.exit(1);
});

// Wait 3 seconds for backend to initialize, then start frontend
setTimeout(() => {
  console.log(`\n${colors.green}[Frontend]${colors.reset} Starting Vite dev server...\n`);
  
  const frontend = spawn('npx', ['vite', '--port', '8082'], {
    cwd: __dirname,
    shell: true,
    stdio: 'inherit',
  });

  frontend.on('error', (err) => {
    console.error(`${colors.yellow}[Frontend Error]${colors.reset}`, err);
    backend.kill();
    process.exit(1);
  });

  // Handle graceful shutdown
  process.on('SIGINT', () => {
    console.log(`\n${colors.yellow}Shutting down...${colors.reset}`);
    backend.kill();
    frontend.kill();
    process.exit(0);
  });
}, 3000);
