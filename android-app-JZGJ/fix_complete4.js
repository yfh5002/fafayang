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
var s = result.join('\n');

// Step 2-3: Replace all escaped quotes
s = s.replace(/\\\\'/g, "'");
s = s.replace(/\\'/g, "'");

// Step 4: Fix onclick patterns
var sLines = s.split('\n');
for (var k = 0; k < sLines.length; k++) {
  var l = sLines[k];
  if (l.indexOf('onclick="') !== -1) {
    var pos = 0;
    var lineResult = '';
    var len = l.length;
    while (pos < len) {
      if (l.substring(pos).indexOf('onclick="') === 0) {
        lineResult += 'onclick="';
        pos += 9;
        while (pos < len) {
          var ch = l[pos];
          if (ch === '"') {
            lineResult += '"';
            pos++;
            break;
          } else if (ch === "'") {
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
    sLines[k] = lineResult;
  }
}
s = sLines.join('\n');

// Step 5: Fix innerHTML assignments that contain nested function calls with ' parameters
// Pattern: innerHTML = '...func('id')...'
// After our replacement, func('id') inside the outer string breaks it
// We need to find these and escape the inner '

// Strategy: find lines containing innerHTML = or innerHTML += where there's a ' 
// inside a string context that's not properly escaped

// For each line, check if it has a string with nested quotes
for (var k = 0; k < sLines.length; k++) {
  var l = sLines[k];
  
  // Look for patterns like: closeModal('something') or document.getElementById('something')
  // that appear inside a string (between ' and ')
  // These are typically in innerHTML assignments
  
  // Pattern: ...innerHTML = '...someFunction('param')...'
  // The 'param' inside breaks the outer string
  
  // Detect: line has = ' and inside it, there's a function call with (' 
  // followed eventually by ')
  // This is complex to parse. Let me just find lines that have an odd number of '
  // which indicates a broken string
  
  var quoteCount = 0;
  var inString = false;
  for (var c = 0; c < l.length; c++) {
    if (l[c] === "'" && (c === 0 || l[c-1] !== '\\')) {
      quoteCount++;
      inString = !inString;
    }
  }
  
  // If odd number of unescaped quotes, the line might have a broken string
  // But this could also be a multi-line string that starts or ends here
  // Let me only check lines that have innerHTML
  if (l.indexOf('innerHTML') !== -1 && quoteCount % 2 !== 0) {
    console.log('Potential broken string at line ' + (k+1) + ' (' + quoteCount + ' quotes):');
    console.log('  ' + l.substring(0, 250));
  }
}

// Now try to compile with better error detection
try {
  new vm.Script(s);
  console.log('SUCCESS!');
  var newContent = prefix + s + '\n' + suffix;
  fs.writeFileSync('d:/XM/android-app-JZGJ/app/src/main/assets/index.html', newContent, 'utf8');
  console.log('File saved.');
} catch(e) {
  console.log('ERROR:', e.message);
  // Better error detection using Function constructor
  try {
    new Function(s);
  } catch(e2) {
    // Function constructor might give better error messages
    console.log('Function error:', e2.message);
    // The stack might have line info
    if (e2.stack) {
      var lines2 = e2.stack.split('\n');
      for (var k = 0; k < lines2.length; k++) {
        if (lines2[k].indexOf('anonymous') !== -1) {
          console.log(lines2[k]);
        }
      }
    }
  }
}
