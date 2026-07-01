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

// Step 3: Fix all multi-line string patterns
// Pattern: xxx.innerHTML = '\n...\n  ';
// After quote replacement, this becomes: xxx.innerHTML = '\n...\n  ';
// We need: xxx.innerHTML = '...'; (single line)

// Strategy: find all lines ending with = ' (potential multi-line starts)
// and join them with the next lines until we find ';

var lines = script.split('\n');
var result = [];
var i = 0;

while (i < lines.length) {
  var line = lines[i];
  
  // Check if this line ends with = ' (assignment opening a multi-line string)
  if (line.match(/=\s*'$/) || line.match(/\+=\s*'$/)) {
    // Collect until we find a line that is just ';
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
      // This is a multi-line string. Join it.
      // First line: xxx.innerHTML = '
      // Middle lines: HTML content
      // Last line: ';
      
      // Get the assignment part (everything before the opening ')
      var firstLine = collected[0];
      var lastQuoteIdx = firstLine.lastIndexOf("'");
      var assignment = firstLine.substring(0, lastQuoteIdx);
      
      // Get the content (middle lines, strip leading/trailing whitespace)
      var contentLines = collected.slice(1, -1);
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

var newScript = result.join('\n');
console.log('Script lines: ' + lines.length + ' -> ' + result.length);

// Verify
try {
  new vm.Script(newScript);
  console.log('SUCCESS!');
  
  var newContent = prefix + newScript + '\n' + suffix;
  fs.writeFileSync('d:/XM/android-app-JZGJ/app/src/main/assets/index.html', newContent, 'utf8');
  console.log('File saved.');
} catch(e) {
  console.log('ERROR:', e.message);
  
  // Binary search for the error
  var lo = 1, hi = result.length;
  while (lo < hi) {
    var mid = Math.floor((lo + hi) / 2);
    try {
      new vm.Script(result.slice(0, mid).join('\n') + '\n});');
      lo = mid + 1;
    } catch(e2) {
      hi = mid;
    }
  }
  console.log('Error near line', lo);
  for (var k = Math.max(0, lo-5); k < Math.min(result.length, lo+5); k++) {
    var marker = (k === lo-1) ? '>>>' : '   ';
    console.log(marker + ' ' + (k+1) + ': ' + result[k].substring(0, 200));
  }
}
