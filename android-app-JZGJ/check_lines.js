const fs = require('fs');
const c = fs.readFileSync('d:/XM/android-app-JZGJ/app/src/main/assets/index.html', 'utf8');
const lines = c.split('\n');
for (var i = 2610; i < 2625; i++) {
  console.log((i+1) + ': ' + lines[i]);
}
