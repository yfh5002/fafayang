var fs = require('fs');
var html = fs.readFileSync('d:/XM/android-app-JZGJ/app/src/main/assets/index_fixed.html', 'utf8');
var scriptRegex = /<script[^>]*>([\s\S]*?)<\/script>/gi;
var matches = [];
var m;
while ((m = scriptRegex.exec(html)) !== null) matches.push(m[1]);
var lines = matches[4].split('\n');

// Show lines around 252
for (var i = 248; i < 260; i++) {
  console.log((i+1) + ': ' + lines[i]);
}
