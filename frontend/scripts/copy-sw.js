const fs = require('fs');
const path = require('path');

// Ensure public/scripts directory exists
const scriptsDir = path.join(process.cwd(), 'public', 'scripts');
if (!fs.existsSync(scriptsDir)) {
  fs.mkdirSync(scriptsDir, { recursive: true });
}

// Copy register-sw.js to public/scripts
fs.copyFileSync(
  path.join(__dirname, 'register-sw.js'),
  path.join(scriptsDir, 'register-sw.js')
);

console.log('Service worker registration script copied to public/scripts');
