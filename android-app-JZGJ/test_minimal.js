var fs = require('fs');
var vm = require('vm');

var path = 'd:/XM/android-app-JZGJ/app/build/intermediates/assets/debug/index.html';
var content = fs.readFileSync(path, 'utf8');

var startMarker = '<script>\n  // ====================';
var startIdx = content.indexOf(startMarker);
var endIdx = content.indexOf('</script>', startIdx + 100);
var script = content.substring(startIdx + '<script>'.length, endIdx);

// ONLY fix multi-line strings, don't touch any quotes
var lines = script.split('\n');
var result = [];
var i = 0;
var fixed = 0;

while (i < lines.length) {
  var line = lines[i];
  // Detect: line ends with = ' or += ' (not \\')
  if (line.match(/=\s*'$/) || line.match(/\+=\s*'$/)) {
    var collected = [line];
    var j = i + 1;
    var found = false;
    while (j < lines.length) {
      collected.push(lines[j]);
      // End patterns: '; or \\';
      if (lines[j].match(/^\s*';\s*$/) || lines[j].match(/^\s*\\';\s*$/)) {
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
      
      // Join middle lines
      var middleLines = collected.slice(1, -1);
      var lastLine = collected[collected.length - 1];
      
      // For the last line, extract just the content (remove '; or \\';)
      var lastContent = lastLine.replace(/^\s*/, '').replace(/\\?\s*';\s*$/, '');
      
      var allContent = middleLines.map(function(l) { return l.trim(); }).join(' ') + ' ' + lastContent;
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

var newScript = result.join('\n');
console.log('Fixed', fixed, 'multi-line strings');

try {
  new vm.Script(newScript);
  console.log('SUCCESS! Multi-line strings were the only syntax issue.');
  // If this works, save this version
  var prefix = content.substring(0, startIdx + '<script>'.length);
  var suffix = content.substring(endIdx);
  var newContent = prefix + newScript + '\n' + suffix;
  fs.writeFileSync('d:/XM/android-app-JZGJ/app/src/main/assets/index.html', newContent, 'utf8');
  console.log('File saved.');
} catch(e) {
  console.log('ERROR:', e.message);
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
