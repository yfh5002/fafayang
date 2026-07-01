var fs = require('fs');
var vm = require('vm');
var html = fs.readFileSync('d:/XM/android-app-JZGJ/app/src/main/assets/index.html', 'utf8');
var scriptRegex = /<script[^>]*>([\s\S]*?)<\/script>/gi;
var matches = [];
var m;
while ((m = scriptRegex.exec(html)) !== null) matches.push(m[1]);

var lines = matches[4].split('\n');

// Show lines around 1113
console.log("=== Around script line 1113 ===");
for (var i = 1108; i < 1140; i++) {
  console.log((i+1) + ": " + lines[i]);
}

// Show lines around 2687
console.log("\n=== Around script line 2687 ===");
for (var i = 2682; i < 2710; i++) {
  console.log((i+1) + ": " + lines[i]);
}
