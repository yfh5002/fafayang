var fs = require('fs');
var vm = require('vm');
var html = fs.readFileSync('d:/XM/android-app-JZGJ/app/src/main/assets/index.html', 'utf8');
var scriptRegex = /<script[^>]*>([\s\S]*?)<\/script>/gi;
var matches = [];
var m;
while ((m = scriptRegex.exec(html)) !== null) matches.push(m[1]);

var scriptContent = matches[4];
var lines = scriptContent.split('\n');

function tryCompile(lineCount) {
  var code = lines.slice(0, lineCount).join('\n');
  var opens = 0;
  for (var i = 0; i < code.length; i++) {
    if (code[i] === '{') opens++;
    else if (code[i] === '}') opens--;
  }
  while (opens > 0) { code += '}'; opens--; }
  code += ';';
  
  try {
    new vm.Script(code);
    return { ok: true };
  } catch(e) {
    return { ok: false, msg: e.message };
  }
}

// Binary search for "Invalid or unexpected token" errors only
var lo = 1, hi = lines.length;
while (lo < hi) {
  var mid = Math.floor((lo + hi) / 2);
  var result = tryCompile(mid);
  if (result.ok || result.msg.indexOf('Invalid') === -1) {
    lo = mid + 1;
  } else {
    hi = mid;
  }
}

console.log('Syntax error near line ' + lo);
for (var i = Math.max(0, lo - 5); i <= Math.min(lines.length - 1, lo + 5); i++) {
  var marker = (i === lo - 1) ? '>>>' : '   ';
  console.log(marker + ' ' + (i + 1) + ': ' + lines[i].substring(0, 150));
}

// Show character details for that line
var line = lines[lo - 1];
console.log('\nCharacter analysis for line ' + lo + ' (' + line.length + ' chars):');
for (var j = Math.max(0, line.length - 30); j < line.length; j++) {
  var c = line[j];
  var code = line.charCodeAt(j);
  var isProblem = (code < 32 && code !== 9) || code === 0 || code === 0xFFFD || code > 127;
  var flag = isProblem ? ' *** PROBLEM ***' : '';
  console.log('  [' + j + '] 0x' + code.toString(16).padStart(4, '0') + ' ' + (isProblem ? '(problem)' : '         ') + ' ' + JSON.stringify(c) + flag);
}
