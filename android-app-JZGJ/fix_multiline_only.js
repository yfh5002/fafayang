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

var lines = script.split('\n');
var result = [];
var i = 0;
var fixed = 0;

while (i < lines.length) {
  var line = lines[i];
  
  // Detect multi-line string starts: ends with = ' or = \' or += ' or += \'
  // Also detect: ends with return ' (for return statements)
  if (line.match(/=\s*\\?'$/) || line.match(/\+=\s*\\?'$/) || line.match(/return\s*\\?'$/)) {
    var collected = [line];
    var j = i + 1;
    var found = false;
    while (j < lines.length) {
      collected.push(lines[j]);
      // End patterns: ';\s*$ or \\';\s*$
      if (lines[j].match(/^\s*';\s*$/) || lines[j].match(/^\s*\\';\s*$/) || lines[j].match(/^\s*'\s*$/)) {
        found = true;
        break;
      }
      j++;
    }
    
    if (found && collected.length > 2) {
      fixed++;
      var firstLine = collected[0];
      // Find the last quote character
      var lastQuoteIdx = firstLine.lastIndexOf("'");
      var assignment = firstLine.substring(0, lastQuoteIdx);
      
      // Remove the leading \' or ' from the assignment suffix
      // The actual quote is at lastQuoteIdx
      assignment = firstLine.substring(0, lastQuoteIdx);
      
      // Get content lines (middle + cleaned last line)
      var contentLines = collected.slice(1, -1);
      var lastLine = collected[collected.length - 1];
      // Remove trailing '; or \';
      var lastClean = lastLine.replace(/^\s*/, '').replace(/\\?\s*';\s*$/, '').replace(/\\?\s*'\s*$/, '');
      
      var allContent = contentLines.map(function(l) { return l.trim(); }).join(' ') + ' ' + lastClean;
      allContent = allContent.replace(/\s+/g, ' ').trim();
      
      result.push(assignment + "'" + allContent + "';");
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

console.log('Fixed', fixed, 'multi-line strings');
var newScript = result.join('\n');

try {
  new vm.Script(newScript);
  console.log('SUCCESS! Only multi-line strings needed fixing.');
  var newContent = prefix + newScript + '\n' + suffix;
  fs.writeFileSync('d:/XM/android-app-JZGJ/app/src/main/assets/index.html', newContent, 'utf8');
  console.log('File saved.');
} catch(e) {
  console.log('ERROR:', e.message);
  // Find the actual error line
  var lo = 1, hi = result.length;
  while (lo < hi) {
    var mid = Math.floor((lo + hi) / 2);
    try { new vm.Script(result.slice(0, mid).join('\n') + '\n}'); lo = mid + 1; }
    catch(e2) { hi = mid; }
  }
  console.log('Error near line', lo);
  for (var k = Math.max(0, lo-5); k < Math.min(result.length, lo+5); k++) {
    var m = (k === lo-1) ? '>>>' : '   ';
    console.log(m + ' ' + (k+1) + ': ' + result[k].substring(0, 250));
  }
}
