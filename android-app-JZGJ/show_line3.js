var fs = require('fs');
var html = fs.readFileSync('d:/XM/android-app-JZGJ/app/src/main/assets/index.html', 'utf8');
var lines = html.split('\n');

// Find the line containing "statusEl.textContent" and "types"
for (var i = 0; i < lines.length; i++) {
  if (lines[i].indexOf('statusEl.textContent') !== -1 && lines[i].indexOf('types') !== -1) {
    console.log('HTML line ' + (i+1) + ':');
    // Show hex of last 20 chars
    var line = lines[i];
    var last20 = line.substring(line.length - 25);
    console.log('  Content: ' + JSON.stringify(last20));
    for (var j = 0; j < last20.length; j++) {
      console.log('  char[' + j + ']: ' + JSON.stringify(last20[j]) + ' (0x' + last20.charCodeAt(j).toString(16) + ')');
    }
  }
}
