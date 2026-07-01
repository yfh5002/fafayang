var fs = require('fs');
var html = fs.readFileSync('d:/XM/android-app-JZGJ/app/src/main/assets/index.html', 'utf8');
var lines = html.split('\n');

// Find lines containing a.date
for (var i = 0; i < lines.length; i++) {
  if (lines[i].indexOf('a.date') !== -1) {
    console.log((i+1) + ': ' + lines[i].trim());
  }
}
