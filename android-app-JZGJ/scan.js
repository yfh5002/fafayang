const fs = require('fs');
const content = fs.readFileSync('d:/XM/android-app-JZGJ/app/src/main/assets/index.html', 'utf8');
const lines = content.split('\n');
console.log('Total lines:', lines.length);

// Search for switchPage, bindEvents, bottom-nav related
const patterns = ['switchPage', 'bindEvents', 'bottom-nav', 'nav-btn', 'bottomNav', 'tab-bar'];
for (const pat of patterns) {
  console.log('\n=== Pattern: ' + pat + ' ===');
  for (let i = 0; i < lines.length; i++) {
    if (lines[i].includes(pat)) {
      console.log((i+1) + ': ' + lines[i].trim().substring(0, 120));
    }
  }
}
