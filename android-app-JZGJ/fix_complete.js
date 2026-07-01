var fs = require('fs');
var vm = require('vm');

var path = 'd:/XM/android-app-JZGJ/app/build/intermediates/assets/debug/index.html';
var content = fs.readFileSync(path, 'utf8');

var startMarker = '<script>\n  // ====================';
var startIdx = content.indexOf(startMarker);
var endIdx = content.indexOf('</script>', startIdx + 100);
var prefix = content.substring(0, startIdx + '<script>'.length);
var suffix = content.substring(endIdx);
var script = content.substring(startIdx + '<script>'.length, endIdx);

// Step 1: Fix multi-line strings (before any quote replacement)
var lines = script.split('\n');
var result = [];
var i = 0;
var fixed = 0;

while (i < lines.length) {
  var line = lines[i];
  if (line.match(/=\s*\\?'$/) || line.match(/\+=\s*\\?'$/) || line.match(/return\s*\\?'$/)) {
    var collected = [line];
    var j = i + 1;
    var found = false;
    while (j < lines.length) {
      collected.push(lines[j]);
      if (lines[j].match(/^\s*';\s*$/) || lines[j].match(/^\s*\\';\s*$/) || lines[j].match(/^\s*'\s*$/)) {
        found = true;
        break;
      }
      j++;
    }
    if (found && collected.length > 2) {
      fixed++;
      var firstLine = collected[0];
      var lastQuoteIdx = firstLine.lastIndexOf("'");
      var assignment = firstLine.substring(0, lastQuoteIdx);
      var contentLines = collected.slice(1, -1);
      var lastLine = collected[collected.length - 1];
      var lastClean = lastLine.replace(/^\s*/, '').replace(/\\?\s*';?\s*$/, '');
      var allContent = contentLines.map(function(l) { return l.trim(); }).join(' ') + ' ' + lastClean;
      allContent = allContent.replace(/\s+/g, ' ').trim();
      result.push(assignment + "'" + allContent + "';");
      i = j + 1;
    } else { result.push(line); i++; }
  } else { result.push(line); i++; }
}
console.log('Step 1: Fixed', fixed, 'multi-line strings');

// Step 2: Replace all \\\\' with '
var s = result.join('\n');
var beforeLen = s.length;
s = s.replace(/\\\\'/g, "'");
console.log('Step 2: Replaced \\\\\\\\ with \', length', beforeLen, '->', s.length);

// Step 3: Replace all \\' with '
var beforeLen2 = s.length;
s = s.replace(/\\'/g, "'");
console.log('Step 3: Replaced \\\\ with nothing, length', beforeLen2, '->', s.length);

// Step 4: Fix onclick= patterns where '' (double single-quotes) break the string
// After steps 2&3, onclick="func('' + var + '')" has '' which breaks the outer JS string
// We need to change these to use escaped quotes inside the outer string
// Pattern in the string: onclick="func(' + var + ')" 
// Should be: onclick="func(\' + var + \')" - but we already removed \' so we can't go back
// Instead, we can use double quotes for the HTML attribute: 
// Or change the outer string to use double quotes
// Or use &apos; in HTML

// The cleanest fix: find onclick="func(' + var + ')" and change to onclick="func(\'' + var + '\')"
// But since we already replaced \' with ', we need to add back the escaping

// Pattern: onclick="...(' + ... + ')"  where ' breaks the outer JS string
// We need to escape the ' that separates the HTML onclick value from JS concatenation

// Let's find lines with onclick= and fix them
var sLines = s.split('\n');
for (var k = 0; k < sLines.length; k++) {
  var l = sLines[k];
  // Find onclick="...(' + ... + ')" patterns
  // The issue: in a JS string like '<div onclick="func(' + var + ')">', the ' inside onclick breaks the outer string
  // Fix: change to '<div onclick="func(\'' + var + '\')">'
  
  // More specifically, find patterns where ' is used inside onclick="..." and it's used for JS function parameters
  if (l.indexOf('onclick=') !== -1) {
    // Find the onclick value boundaries
    // This is complex to parse correctly. Let me use a simpler approach:
    // In these lines, replace ' + ... + ' with \' + ... + \' ONLY when inside an onclick="..." context
    
    // Actually, the simplest approach: replace the onclick HTML attributes to use &apos; instead of '
    // onclick="selectBackupPath(' + opt.path + ')" -> onclick="selectBackupPath(&apos;' + opt.path + '&apos;)"
    // But this would also break the JS concatenation...
    
    // Better approach: change onclick="func(' + var + ')" to onclick='func(" + var + ")'
    // i.e., use single quotes for the HTML attribute and double quotes for the JS strings inside
    
    // Actually, the cleanest is: since the outer JS string uses ', we should use " for the onclick attribute
    // and ' inside the onclick should be escaped as \'
    // onclick="func(' + var + ')" -> onclick="func(\'' + var + '\')"
    
    // Let me do a targeted replacement:
    // Find: onclick="X(' + Y + ')" and replace ' inside with \'
    sLines[k] = l.replace(/onclick="(.*?)\('([^)]*)\+\s*([^)]*)\+\s*([^)]*)'\)"/g, 
      function(m, before, p1, p2, p3) {
        // Reconstruct with escaped quotes
        return 'onclick="' + before + '(\\' + p1 + ' + ' + p2 + ' + ' + p3 + '\\\')"';
      });
    
    // Also handle simpler patterns: onclick="func(' + var + ')"
    sLines[k] = sLines[k].replace(/onclick="(\w+)\('([^)]*)\+\s*(\w+)\+\s*([^)]*)'\)"/g,
      function(m, func, before, mid, after) {
        return 'onclick="' + func + '(\\' + before + ' + ' + mid + ' + ' + after + '\\\')"';
      });
  }
}

s = sLines.join('\n');

// Step 5: Fix other known patterns with similar issues (event handlers, etc.)
// closeModal('xxx');document.getElementById('xxx') in innerHTML strings
// After our replacements, these became: closeModal('xxx');document.getElementById('xxx')
// But inside a JS string, these ' need to be \'

// Let me also fix patterns where ' appears inside innerHTML strings for DOM manipulation
// Pattern: innerHTML = '...getElementById('id')...'
// The getElementById('id') is inside the outer JS string, so ' needs to be \'

// This is getting really complex. Let me try a different approach.
// Instead of fixing individual patterns, let me check if the current script compiles.

try {
  new vm.Script(s);
  console.log('SUCCESS!');
  var newContent = prefix + s + '\n' + suffix;
  fs.writeFileSync('d:/XM/android-app-JZGJ/app/src/main/assets/index.html', newContent, 'utf8');
  console.log('File saved.');
} catch(e) {
  console.log('ERROR:', e.message);
  var sLines2 = s.split('\n');
  var lo = 1, hi = sLines2.length;
  while (lo < hi) {
    var mid = Math.floor((lo + hi) / 2);
    try { new vm.Script(sLines2.slice(0, mid).join('\n') + '\n}'); lo = mid + 1; }
    catch(e2) { hi = mid; }
  }
  console.log('Error near line', lo);
  for (var k = Math.max(0, lo-3); k < Math.min(sLines2.length, lo+3); k++) {
    var m = (k === lo-1) ? '>>>' : '   ';
    console.log(m + ' ' + (k+1) + ': ' + sLines2[k].substring(0, 300));
  }
}
