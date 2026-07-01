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

// Step 1: Fix multi-line strings
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
      if (lines[j].match(/^\s*';\s*$/) || lines[j].match(/^\s*\\';\s*$/) || lines[j].match(/^\s*'\s*$/)) { found = true; break; }
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

// Step 2: Replace \\\\' with '
s = s.replace(/\\\\'/g, "'");
// Step 3: Replace \\' with '
s = s.replace(/\\'/g, "'");
console.log('Steps 2-3: Replaced all escaped quotes');

// Step 4: Fix onclick= and other HTML event handler patterns
// After replacing \' with ', patterns like:
//   '<div onclick="func(' + var + ')">'
// became broken because the ' inside onclick breaks the outer string.
//
// We need to find ALL ' that appear inside onclick="..." or similar HTML attribute contexts
// and re-escape them to \'
//
// Strategy: For each line, find onclick="..." and within it, re-escape '
// But we need to know which ' are inside the onclick value vs the outer JS string delimiter

// The pattern we're looking for:
// Outer JS: '... onclick="..." ...'
// Inside onclick: func(' + var + ')
// The ' inside onclick value breaks the outer JS string

// Better strategy: use a simple state machine to track string nesting
// For each line, find sequences like: onclick="..." and re-escape quotes inside

var sLines = s.split('\n');
var fixCount = 0;

for (var k = 0; k < sLines.length; k++) {
  var l = sLines[k];
  var newLine = '';
  var inOuterString = false;
  var outerStringChar = '';
  var inAttrValue = false;
  var attrQuoteChar = '';
  
  // Simple approach: scan the line character by character
  // When we're inside a JS string delimited by ', and we encounter onclick=",
  // everything between " and the closing " is an HTML attribute value.
  // Inside that attribute value, ' should be re-escaped to \'
  
  // Even simpler: use regex to find onclick="...(' + var + ')" and fix them
  // The key pattern: after onclick=", there's content with ' that should be \'
  
  // Let me use a different regex approach:
  // Find: '= '...onclick="...(' + ... + ')"...'
  // And re-escape the ' inside onclick value
  
  // Pattern: in a line like:
  // optionsHtml += '<div onclick="selectBackupPath('' + opt.path + '')">';
  // We want to change the onclick="..." part so that ' inside becomes \'
  
  // Regex approach: find onclick="..." and replace ' within it with \'
  // But we need to be careful not to match the outer string delimiter '
  
  // The key insight: inside onclick="...", we can use ' freely in HTML
  // But in a JS string delimited by ', the ' in onclick breaks the string
  // So we need to escape ALL ' that appear between onclick=" and the closing "
  
  // Let me use a manual parser for each line
  var pos = 0;
  var lineResult = '';
  var len = l.length;
  
  while (pos < len) {
    // Check for onclick=" pattern
    if (l.substring(pos).indexOf('onclick="') === 0) {
      lineResult += 'onclick="';
      pos += 9; // skip 'onclick="'
      
      // Now read until closing " (but handle escaped quotes)
      while (pos < len) {
        var ch = l[pos];
        if (ch === '"') {
          // Closing quote of the attribute
          lineResult += '"';
          pos++;
          break;
        } else if (ch === "'" && !inAttrValue) {
          // A ' inside the onclick value - need to escape it
          lineResult += "\\'";
          pos++;
        } else {
          lineResult += ch;
          pos++;
        }
      }
    } else {
      lineResult += l[pos];
      pos++;
    }
  }
  
  if (lineResult !== l) {
    fixCount++;
    sLines[k] = lineResult;
  }
}
console.log('Step 4: Fixed', fixCount, 'onclick patterns');

// Step 5: Also fix similar patterns for other event handlers
// event.stopPropagation(); openSomething('id'); etc. inside innerHTML strings
// These patterns also have ' that breaks the outer string

// For now, let me check if the onclick fix was enough

s = sLines.join('\n');

try {
  new vm.Script(s);
  console.log('SUCCESS!');
  var newContent = prefix + s + '\n' + suffix;
  fs.writeFileSync('d:/XM/android-app-JZGJ/app/src/main/assets/index.html', newContent, 'utf8');
  console.log('File saved. Lines: ' + s.split('\n').length);
} catch(e) {
  console.log('ERROR:', e.message);
  var sLines2 = s.split('\n');
  var lo = 1, hi = sLines2.length;
  while (lo < hi) {
    var mid = Math.floor((lo + hi) / 2);
    try { new vm.Script(sLines2.slice(0, mid).join('\n')); lo = mid + 1; }
    catch(e2) { hi = mid; }
  }
  console.log('Error near line', lo);
  for (var k = Math.max(0, lo-3); k < Math.min(sLines2.length, lo+3); k++) {
    var m = (k === lo-1) ? '>>>' : '   ';
    console.log(m + ' ' + (k+1) + ': ' + sLines2[k].substring(0, 300));
  }
}
