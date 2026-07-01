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

// Step 1: Replace \\\\' with '
script = script.replace(/\\\\'/g, "'");
// Step 2: Replace \\' with '
script = script.replace(/\\'/g, "'");

// Step 3: Fix multi-line strings (those starting with = ' or += ')
var lines = script.split('\n');
var result = [];
var i = 0;
var multiCount = 0;

while (i < lines.length) {
  var line = lines[i];
  // Detect multi-line string: line ends with = ' or += '
  if (/(?:\+?=|className)\s*'[^']*$/.test(line) && !/'[^']*$/.test(line.substring(0, line.lastIndexOf("'") !== -1 ? line.lastIndexOf("'") : 0))) {
    // Simpler: just check if line ends with = ' or += '
  }
  if (line.match(/=\s*'$/) || line.match(/\+=\s*'$/)) {
    var collected = [line];
    var j = i + 1;
    var found = false;
    while (j < lines.length) {
      collected.push(lines[j]);
      // Look for line that is just '; (which ends the string)
      if (lines[j].match(/^\s*';\s*$/)) {
        found = true;
        break;
      }
      // Also check for lines that end with ';
      if (lines[j].match(/';\s*$/) && j > i + 1) {
        // This line has content AND ends with '; - might be the end
        // Check if this looks like string content (has HTML tags)
        if (lines[j].indexOf('<') !== -1 || lines[j].indexOf('>') !== -1 || lines[j].indexOf('+') !== -1) {
          found = true;
          break;
        }
      }
      j++;
    }
    
    if (found && collected.length > 2) {
      multiCount++;
      var firstLine = collected[0];
      var lastQuoteIdx = firstLine.lastIndexOf("'");
      var assignment = firstLine.substring(0, lastQuoteIdx);
      
      var contentLines = collected.slice(1);
      // The last line should end with '; - remove it
      var lastLine = contentLines[contentLines.length - 1];
      lastLine = lastLine.replace(/'\s*$/, ''); // Remove trailing '
      contentLines[contentLines.length - 1] = lastLine;
      
      var joined = contentLines.map(function(l) { return l.trim(); }).join(' ');
      result.push(assignment + "'" + joined + "';");
      i = j + 1;
    } else {
      result.push(line);
      i++;
    }
  } else {
    result.push(line);
    i++;
  }
}

console.log('Fixed', multiCount, 'multi-line strings');

var newScript = result.join('\n');

// Step 4: Fix HTML onclick attributes that now have '' (empty string) instead of '
// Pattern: onclick="function('' + var + '')" should be onclick="function(' + var + ')"
// After our replacements: onclick="function('' + var + '')" 
// Should be: onclick="function(' + var + ')"
// But wait - we can't use bare ' inside a JS string that's delimited with '
// The correct approach for HTML in JS strings is:
// '<tag onclick="func(\'' + var + '\')">' — escaped quotes inside JS string

// After our global replace, onclick="func('' + var + '')" became onclick="func(' + var + ')"
// But inside a JS ' string, the ' will terminate the string!
// So we need to escape them back: replace ' + var + ' with \' + var + \' ONLY inside JS strings that are building HTML

// Actually, let me think about this differently.
// The pattern in the original was:
// '<div onclick="selectBackupPath(\'' + opt.path + '\')">'
// In the file: \\\\' for each \' 
// After our replace: '<div onclick="selectBackupPath('' + opt.path + '')">'
// Which in JS means: string starts with ', content is <div onclick="selectBackupPath(, then '' is empty string, + opt.path +, then '' is empty string, then )">
// But the ' in selectBackupPath(' ends the outer string!

// So we need to find these patterns and fix them.
// Pattern: onclick="func('' + var + '')" -> onclick="func(\'' + var + '\')"
// More generally: inside onclick="...", bare ' that separates from JS concatenation should be escaped

// Let me find all lines with onclick= and fix the quoting
newScript = newScript.replace(/onclick="([^"]+)"/g, function(match, inner) {
  // Inside the onclick, find patterns like ('' + var + '')
  // These should be (\'' + var + '\'')
  return match.replace(/'\s*\+\s*/g, "'\\' + ").replace(/\+\s*'/g, " + \\'");
});

// Also fix oninput= and other event handlers
// Actually, let me also fix patterns like: getElementById('path-picker-modal')
// These should already be fine after our global replace.

// Step 5: Fix other known patterns
// Patterns like: getElementById('something') should work
// But patterns like: getElementById(\'something\') need the \' -> '

// Let me check what's left
var remaining = newScript.match(/\\'/g);
console.log('Remaining \\\\:', remaining ? remaining.length : 0);

try {
  new vm.Script(newScript);
  console.log('SUCCESS!');
  var newContent = prefix + newScript + '\n' + suffix;
  fs.writeFileSync('d:/XM/android-app-JZGJ/app/src/main/assets/index.html', newContent, 'utf8');
  console.log('File saved.');
} catch(e) {
  console.log('ERROR:', e.message);
  var lines2 = newScript.split('\n');
  var lo = 1, hi = lines2.length;
  while (lo < hi) {
    var mid = Math.floor((lo + hi) / 2);
    try { new vm.Script(lines2.slice(0, mid).join('\n') + '\n}'); lo = mid + 1; }
    catch(e2) { hi = mid; }
  }
  console.log('Error near line', lo);
  for (var k = Math.max(0, lo-5); k < Math.min(lines2.length, lo+5); k++) {
    var m = (k === lo-1) ? '>>>' : '   ';
    console.log(m + ' ' + (k+1) + ': ' + lines2[k].substring(0, 250));
  }
}
