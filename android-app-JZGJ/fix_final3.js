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

// Step 3: Fix multi-line strings
var lines = script.split('\n');
var result = [];
var i = 0;

while (i < lines.length) {
  var line = lines[i];
  
  if (line.match(/=\s*'$/) || line.match(/\+=\s*'$/)) {
    var collected = [line];
    var j = i + 1;
    var found = false;
    while (j < lines.length) {
      collected.push(lines[j]);
      if (lines[j].match(/^\s*';\s*$/)) {
        found = true;
        break;
      }
      j++;
    }
    
    if (found && collected.length > 2) {
      var firstLine = collected[0];
      var lastQuoteIdx = firstLine.lastIndexOf("'");
      var assignment = firstLine.substring(0, lastQuoteIdx);
      var contentLines2 = collected.slice(1, -1);
      var joined = contentLines2.map(function(l) { return l.trim(); }).join(' ');
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

var newScript = result.join('\n');

// Check each line for potential issues
for (var k = 0; k < newScript.length; k++) {
  // Look for unescaped quotes that might cause issues
}

// Try to compile incrementally to find the exact error
var testScript = '';
var errorLine = -1;
for (var k = 0; k < result.length; k++) {
  testScript += result[k] + '\n';
  try {
    // Just check if it's parseable so far
    try {
      new vm.Script(testScript + '\n//EOF');
    } catch(e) {
      if (e.message.includes('Invalid') || e.message.includes('Unexpected') || e.message.includes('unexpected')) {
        errorLine = k + 1;
        // Print context
        for (var l = Math.max(0, k-3); l <= Math.min(result.length-1, k+3); l++) {
          var m = (l === k) ? '>>>' : '   ';
          console.log(m + ' ' + (l+1) + ': ' + result[l].substring(0, 200));
        }
        console.log('Error: ' + e.message);
        break;
      }
    }
  } catch(e2) {
    // ignore
  }
}

if (errorLine === -1) {
  console.log('No errors found in incremental check!');
  try {
    new vm.Script(newScript);
    console.log('FULL COMPILATION SUCCESS!');
    var newContent = prefix + newScript + '\n' + suffix;
    fs.writeFileSync('d:/XM/android-app-JZGJ/app/src/main/assets/index.html', newContent, 'utf8');
    console.log('File saved.');
  } catch(e3) {
    console.log('Full compilation error:', e3.message);
  }
} else {
  console.log('First error at line', errorLine);
}
