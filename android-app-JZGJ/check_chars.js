var fs = require('fs');
var vm = require('vm');
var html = fs.readFileSync('d:/XM/android-app-JZGJ/app/src/main/assets/index.html', 'utf8');
var scriptRegex = /<script[^>]*>([\s\S]*?)<\/script>/gi;
var matches = [];
var m;
while ((m = scriptRegex.exec(html)) !== null) matches.push(m[1]);

var scriptContent = matches[4];
var lines = scriptContent.split('\n');

// Check each line individually for invalid tokens
for (var i = 0; i < Math.min(lines.length, 20); i++) {
  var line = lines[i];
  // Check for non-ASCII or problematic characters
  for (var j = 0; j < line.length; j++) {
    var code = line.charCodeAt(j);
    if (code === 0 || code < 32 && code !== 9 && code !== 10 && code !== 13) {
      console.log('Line ' + (i+1) + ', char ' + j + ': INVALID char 0x' + code.toString(16));
    }
  }
  console.log('Line ' + (i+1) + ' (' + line.length + ' chars): ' + line.substring(0, 80));
}

// Try compiling first 20 lines
console.log('\nTrying first 20 lines...');
try {
  new vm.Script(lines.slice(0, 20).join('\n'));
  console.log('First 20 lines: OK');
} catch(e) {
  console.log('First 20 lines: ERROR - ' + e.message);
}

// Try to find the exact line by adding one at a time
console.log('\nIncremental check...');
for (var i = 1; i <= 30; i++) {
  try {
    new vm.Script(lines.slice(0, i).join('\n'));
  } catch(e) {
    console.log('Fails at line ' + i + ': ' + e.message);
    break;
  }
}
