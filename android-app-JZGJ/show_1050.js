var fs = require('fs');
var html = fs.readFileSync('d:/XM/android-app-JZGJ/app/src/main/assets/index_fixed2.html', 'utf8');
var scriptRegex = /<script[^>]*>([\s\S]*?)<\/script>/gi;
var matches = [];
var m;
while ((m = scriptRegex.exec(html)) !== null) matches.push(m[1]);
var lines = matches[4].split('\n');

// Show line 1050
console.log('Line 1050: ' + lines[1049]);
console.log('Line 1049: ' + lines[1048]);
console.log('Line 1051: ' + lines[1050]);
