var fs = require('fs');
var vm = require('vm');
var html = fs.readFileSync('d:/XM/android-app-JZGJ/app/src/main/assets/index.html', 'utf8');
var scriptRegex = /<script[^>]*>([\s\S]*?)<\/script>/gi;
var matches = [];
var m;
while ((m = scriptRegex.exec(html)) !== null) matches.push(m[1]);

var scriptContent = matches[4];
var lines = scriptContent.split('\n');

// Better binary search: use try-catch with balanced braces
function tryCompile(lineCount) {
  var code = lines.slice(0, lineCount).join('\n');
  // Count open braces and add closing
  var opens = 0;
  for (var i = 0; i < code.length; i++) {
    if (code[i] === '{') opens++;
    else if (code[i] === '}') opens--;
  }
  // Add closing braces and semicolon
  while (opens > 0) { code += '}'; opens--; }
  code += ';';
  
  try {
    new vm.Script(code);
    return true;
  } catch(e) {
    return false;
  }
}

// Find exact failing line
var lo = 1, hi = lines.length;
while (lo < hi) {
  var mid = Math.floor((lo + hi) / 2);
  if (tryCompile(mid)) {
    lo = mid + 1;
  } else {
    hi = mid;
  }
}

console.log('First error at line ' + lo);
for (var i = Math.max(0, lo - 3); i <= Math.min(lines.length - 1, lo + 3); i++) {
  console.log('  ' + (i + 1) + ': ' + lines[i]);
}

// Try just that line
console.log('\nTrying just line ' + lo + '...');
try {
  new vm.Script(lines[lo - 1]);
  console.log('Line alone: OK');
} catch(e) {
  console.log('Line alone: ERROR - ' + e.message);
}

// Try lines around it
console.log('\nTrying lines ' + (lo-1) + ' to ' + (lo+1) + '...');
try {
  var testCode = lines.slice(lo - 2, lo + 1).join('\n');
  new vm.Script(testCode);
  console.log('Lines ' + (lo-1) + '-' + (lo+1) + ': OK');
} catch(e) {
  console.log('Lines ' + (lo-1) + '-' + (lo+1) + ': ERROR - ' + e.message);
}
