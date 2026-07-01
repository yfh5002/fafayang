var fs = require('fs');
var vm = require('vm');

var content = fs.readFileSync('d:/XM/android-app-JZGJ/app/src/main/assets/index.html', 'utf8');

// Find the main script block
var startMarker = '<script>\n  // ====================';
var startIdx = content.indexOf(startMarker);
var endIdx = content.indexOf('</script>', startIdx + 100);
var prefix = content.substring(0, startIdx + '<script>'.length);
var suffix = content.substring(endIdx);
var script = content.substring(startIdx + '<script>'.length, endIdx);

// The fix:
// 1. In the file, \' should be ' (normal single quote)
// 2. The multi-line innerHTML on line 2612 needs to be a single line

// Step 1: Fix the multi-line innerHTML (empty state)
// Pattern: innerHTML = '\n  <div ...>...</div>\n  \\';
// Replace with single line
var multiLinePattern = /elements\.recentTransactions\.innerHTML = '\s*\n(\s*<div[\s\S]*?<\/div>)\s*\n\s*\\'/;
var match = script.match(multiLinePattern);
if (match) {
  var htmlContent = match[1].replace(/\s+/g, ' ').trim();
  var replacement = "elements.recentTransactions.innerHTML = '" + htmlContent + "';";
  script = script.replace(multiLinePattern, replacement);
  console.log('Fixed multi-line innerHTML (empty state)');
} else {
  console.log('WARNING: Could not find multi-line innerHTML pattern');
  // Maybe it was already fixed by the previous script
}

// Step 2: Fix all \' -> ' in the script
// But we need to be careful: inside string literals, \' might be intentional
// However, based on the analysis, ALL \' in this file are meant to be plain '
// because the HTML content uses single-quote delimited JS strings

// Replace \' with ' everywhere in the script
// In the file, the literal bytes are \ and ', we want just '
script = script.replace(/\\'/g, "'");

// Now verify
try {
  new vm.Script(script);
  console.log('SUCCESS: Script compiles without errors!');
  
  var newContent = prefix + script + '\n' + suffix;
  fs.writeFileSync('d:/XM/android-app-JZGJ/app/src/main/assets/index.html', newContent, 'utf8');
  console.log('File saved. Total script length: ' + script.length);
} catch(e) {
  console.log('ERROR:', e.message);
  // Show context
  var lines = script.split('\n');
  var stackLines = e.stack.split('\n');
  for (var i = 0; i < stackLines.length; i++) {
    var m = stackLines[i].match(/<anonymous>:(\d+):(\d+)/);
    if (m) {
      var lineNum = parseInt(m[1]);
      for (var j = Math.max(0, lineNum - 5); j < Math.min(lines.length, lineNum + 5); j++) {
        var marker = (j === lineNum - 1) ? '>>>' : '   ';
        console.log(marker + ' ' + (j+1) + ': ' + lines[j].substring(0, 200));
      }
      break;
    }
  }
  console.log('File NOT saved.');
}
