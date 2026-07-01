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

// Step 1: Fix multi-line strings FIRST (before any quote replacement)
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

var s = result.join('\n');

// Step 2: Replace \\\\' (4 bytes: \\ + ') with '
// In file: \\\\ = \\  -> in JS: \' (escaped quote, = literal ' inside string)
// But this is WRONG when used outside strings. We want plain '
var count2 = 0;
s = s.replace(/\\\\'/g, function() { count2++; return "'"; });
console.log('Step 2: Replaced', count2, 'occurrences of \\\\\\\\ with \'');

// Step 3: Replace \\' (2 bytes: \' in file -> \' in JS = escaped quote) with '
// In JS: \' inside a string = literal '
// Outside a string: \' = syntax error
// We want it to be ' in all cases
var count3 = 0;
s = s.replace(/\\'/g, function() { count3++; return "'"; });
console.log("Step 3: Replaced " + count3 + " occurrences of \\' with '");

// Step 4: Now fix lines where our replacement broke string concatenation in HTML contexts
// After steps 2&3, patterns like: onclick="func('' + var + '')" appeared
// Because original: onclick="func(\\\\' + var + \\\\')"
// -> Step 2: onclick="func(' + var + ')"
// But inside the outer JS string, ' terminates the string!
// We need to fix: onclick="func(' + var + ')" -> onclick="func(\' + var + \')"

// Approach: find onclick="..." and re-escape the quotes inside
var sLines = s.split('\n');
var fixCount = 0;
for (var k = 0; k < sLines.length; k++) {
  var l = sLines[k];
  if (l.indexOf("onclick=") !== -1) {
    // Find the onclick=" value
    // Pattern: onclick="something(' + var + ')"
    // The ' inside the onclick breaks the outer JS string
    // Fix: replace ' that's part of HTML onclick attribute value with \'
    
    // Strategy: Find onclick="...", then within it, find patterns like '(' ... '+' ... ')'
    // and escape the quotes around the JS expression
    
    // Simpler: just re-escape all ' that appear between onclick=" and the closing "
    // But this would also escape legitimate quotes in the HTML...
    
    // Let me use a more targeted approach:
    // onclick="func(' + var + ')" -> onclick="func(\'' + var + '\')"
    
    // Match: onclick="...(' + ... + ')"
    var newLine = l.replace(/onclick="([^"]*)\(([^)]+)\+\s*(\w[\w.]*)\+\s*([^)]+)\)\s*"/g,
      function(m, before, p1, p2, p3) {
        return 'onclick="' + before + '(\\' + p1 + ' + ' + p2 + ' + ' + p3 + '\\\')"';
      });
    
    if (newLine !== l) {
      fixCount++;
      sLines[k] = newLine;
    }
  }
}
console.log('Step 4: Fixed', fixCount, 'onclick patterns');

// Also fix similar patterns with other event handlers
for (var k = 0; k < sLines.length; k++) {
  var l = sLines[k];
  // closeModal('xxx');document.getElementById('xxx') inside strings
  // These patterns have ' that breaks the outer string
  // Pattern: inside a string like: "...closeModal('path-picker-modal');document.getElementById('path-pic..."
  // The ' before path-picker-modal closes the outer string
  
  // Detect: lines that have a string starting with ' and inside them another ' from a function call
  // This is hard to detect automatically. Let me check if the current version compiles first.
}

s = sLines.join('\n');

// Step 5: Fix modal.innerHTML and similar innerHTML assignments that have nested quotes
// Pattern: innerHTML = '...getElementById('id')...'
// After our replacements, getElementById('id') inside the outer string breaks it
// We need to re-escape those inner quotes

// Find patterns like: = '...(' + ... + ')'...';
// where the (' starts a function call inside a string
// These inner (' and ') should be \(\'  and \'\) 
// But only when they're inside a JS string context

// For now, let me just try to compile and see what errors remain
try {
  new vm.Script(s);
  console.log('SUCCESS!');
  var newContent = prefix + s + '\n' + suffix;
  fs.writeFileSync('d:/XM/android-app-JZGJ/app/src/main/assets/index.html', newContent, 'utf8');
  console.log('File saved. Total lines: ' + s.split('\n').length);
} catch(e) {
  console.log('ERROR:', e.message);
  var sLines2 = s.split('\n');
  // Use a more accurate binary search
  var lo = 1, hi = sLines2.length;
  while (lo < hi) {
    var mid = Math.floor((lo + hi) / 2);
    try { 
      new vm.Script(sLines2.slice(0, mid).join('\n'));
      lo = mid + 1;
    } catch(e2) { 
      hi = mid; 
    }
  }
  console.log('Error near line', lo);
  for (var k = Math.max(0, lo-3); k < Math.min(sLines2.length, lo+3); k++) {
    var m = (k === lo-1) ? '>>>' : '   ';
    console.log(m + ' ' + (k+1) + ': ' + sLines2[k].substring(0, 300));
  }
  
  // Count remaining \' 
  var remaining = s.match(/\\'/g);
  console.log('Remaining escaped quotes:', remaining ? remaining.length : 0);
}
