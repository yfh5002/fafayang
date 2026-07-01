var fs = require('fs');
var vm = require('vm');

// Read the debug build version (it's the cleanest available)
var path = 'd:/XM/android-app-JZGJ/app/build/intermediates/assets/debug/index.html';
var content = fs.readFileSync(path, 'utf8');

// Find the main script block
var startMarker = '<script>\n  // ====================';
var startIdx = content.indexOf(startMarker);
var endIdx = content.indexOf('</script>', startIdx + 100);
var prefix = content.substring(0, startIdx + '<script>'.length);
var suffix = content.substring(endIdx);
var script = content.substring(startIdx + '<script>'.length, endIdx);

console.log('Original script length:', script.length);

// The comprehensive fix:
// In this file, the quoting is double-escaped. The patterns are:
//
// Pattern A: \\\\'value\\\\'  (in file: \\ + ' = in JS: \' which is escaped quote inside string)
//   These appear in string concatenation contexts like:
//   document.createElement(\\\\'div\\\\')
//   onclick=\\\"editAttendanceRecord(\\\\'' + id + '\\\\')
//
// Pattern B: \\'value\\'  (in file: \' = in JS: \' = escaped quote)
//   These appear in:
//   style.display = 'block\\';
//
// Pattern C: 'value'  (normal single quotes - these are correct)
//
// Pattern D: Multi-line strings starting with ' at end of line
//
// The problem: Both patterns A and B produce \' in JS source code,
// which is only valid INSIDE a string. But many of these appear in
// contexts where they should be plain ' (string delimiters).
//
// Solution: Replace ALL \\' and \\\\' with plain '

// Step 1: Replace \\\\' (four chars: \\\') with '
script = script.replace(/\\\\'/g, "'");

// Step 2: Replace \\' (two chars: \') with '  
script = script.replace(/\\'/g, "'");

// Step 3: Fix the multi-line innerHTML for empty state
// After step 1&2, it will look like: elements.recentTransactions.innerHTML = '\n  <div...>\n  ';
// We need to collapse it to one line
var multiLineEmptyState = /elements\.recentTransactions\.innerHTML = '\s*\n([\s\S]*?)';/;
var m1 = script.match(multiLineEmptyState);
if (m1) {
  var htmlContent = m1[1].replace(/\s*\n\s*/g, ' ').replace(/\s+/g, ' ').trim();
  script = script.replace(multiLineEmptyState, 
    "elements.recentTransactions.innerHTML = '" + htmlContent + "';");
  console.log('Fixed multi-line empty state innerHTML');
}

// Step 4: Fix other multi-line innerHTML patterns
// These follow the pattern: xxx.innerHTML = '\n  ...content...\n  ';
var multiLinePattern = /(\w+)\.innerHTML = '\s*\n([\s\S]*?)';\s*\n/g;
script = script.replace(multiLinePattern, function(match, obj, inner) {
  var fixed = inner.replace(/\s*\n\s*/g, ' ').replace(/\s+/g, ' ').trim();
  return obj + ".innerHTML = '" + fixed + "';\n";
});

// Step 5: Fix html += ' multi-line patterns
var htmlAddPattern = /(\w+)\.innerHTML \+= '\s*\n([\s\S]*?)';\s*\n/g;
script = script.replace(htmlAddPattern, function(match, obj, inner) {
  var fixed = inner.replace(/\s*\n\s*/g, ' ').replace(/\s+/g, ' ').trim();
  return obj + ".innerHTML += '" + fixed + "';\n";
});

// Step 6: Fix html += ' patterns  
var htmlPlusPattern = /html \+= '\s*\n([\s\S]*?)';\s*\n/g;
script = script.replace(htmlPlusPattern, function(match, inner) {
  var fixed = inner.replace(/\s*\n\s*/g, ' ').replace(/\s+/g, ' ').trim();
  return "html += '" + fixed + "';\n";
});

console.log('Fixed script length:', script.length);

// Verify
try {
  new vm.Script(script);
  console.log('SUCCESS: Script compiles without errors!');
  
  // Also fix the multi-line patterns in the full HTML (for non-script areas)
  // Save to the assets directory
  var newContent = prefix + script + '\n' + suffix;
  fs.writeFileSync('d:/XM/android-app-JZGJ/app/src/main/assets/index.html', newContent, 'utf8');
  console.log('File saved to assets/index.html');
} catch(e) {
  console.log('ERROR:', e.message);
  var lines = script.split('\n');
  var stackLines = e.stack.split('\n');
  for (var i = 0; i < stackLines.length; i++) {
    var m = stackLines[i].match(/<anonymous>:(\d+):(\d+)/);
    if (m) {
      var lineNum = parseInt(m[1]);
      console.log('At script line', lineNum);
      for (var j = Math.max(0, lineNum - 5); j < Math.min(lines.length, lineNum + 5); j++) {
        var marker = (j === lineNum - 1) ? '>>>' : '   ';
        console.log(marker + ' ' + (j+1) + ': ' + lines[j].substring(0, 200));
      }
      break;
    }
  }
  console.log('File NOT saved.');
}
