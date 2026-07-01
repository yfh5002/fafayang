var fs = require('fs');
var vm = require('vm');
var html = fs.readFileSync('d:/XM/android-app-JZGJ/app/src/main/assets/index.html', 'utf8');
var scriptRegex = /<script[^>]*>([\s\S]*?)<\/script>/gi;
var matches = [];
var m;
while ((m = scriptRegex.exec(html)) !== null) matches.push(m[1]);
var lines = matches[4].split('\n');

// Show line 1049
for (var i = 1045; i < 1055; i++) {
  console.log((i+1) + ': ' + lines[i]);
}
