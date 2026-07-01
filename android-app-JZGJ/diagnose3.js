var fs = require('fs');
var vm = require('vm');
var html = fs.readFileSync('d:/XM/android-app-JZGJ/app/src/main/assets/index.html', 'utf8');
var scriptRegex = /<script[^>]*>([\s\S]*?)<\/script>/gi;
var matches = [];
var m;
while ((m = scriptRegex.exec(html)) !== null) matches.push(m[1]);

var scriptContent = matches[4];
var lines = scriptContent.split('\n');

// Use binary search with line-at-a-time to find exact error
var lo = 1, hi = lines.length;
var errLine = -1;

// First try the full thing
try {
  new vm.Script(scriptContent);
  console.log('No errors!');
  process.exit(0);
} catch(e) {
  console.log('Error: ' + e.message);
}

// Binary search for the error
while (lo < hi) {
  var mid = Math.floor((lo + hi) / 2);
  var partial = lines.slice(0, mid).join('\n') + '\n});';
  
  try {
    new vm.Script(partial);
    lo = mid + 1; // Error is after mid
  } catch(e) {
    hi = mid; // Error is at or before mid
  }
}

console.log('Error is at or near line ' + lo);
// Show context
for (var i = Math.max(0, lo - 5); i <= Math.min(lines.length - 1, lo + 5); i++) {
  console.log('  ' + (i + 1) + ': ' + lines[i].substring(0, 150));
}
