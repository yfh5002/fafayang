var fs = require('fs');
var vm = require('vm');

var path = 'd:/XM/android-app-JZGJ/app/build/intermediates/assets/debug/index.html';
var content = fs.readFileSync(path, 'utf8');

var startMarker = '<script>\n  // ====================';
var startIdx = content.indexOf(startMarker);
var endIdx = content.indexOf('</script>', startIdx + 100);
var script = content.substring(startIdx + '<script>'.length, endIdx);

// Apply the same transforms
var s = script.replace(/\\\\'/g, "'");
s = s.replace(/\\'/g, "'");

// Fix multi-line strings
var lines = s.split('\n');
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
      if (lines[j].match(/^\s*';\s*$/)) { found = true; break; }
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
    } else { result.push(line); i++; }
  } else { result.push(line); i++; }
}

var newScript = result.join('\n');

// Use Function constructor for better error messages
try {
  new Function(newScript);
  console.log('SUCCESS!');
  var prefix = content.substring(0, startIdx + '<script>'.length);
  var suffix = content.substring(endIdx);
  var newContent = prefix + newScript + '\n' + suffix;
  fs.writeFileSync('d:/XM/android-app-JZGJ/app/src/main/assets/index.html', newContent, 'utf8');
  console.log('Saved!');
} catch(e) {
  console.log('Error:', e.message);
  
  // Try to get line number from the error
  var lineMatch = e.stack ? e.stack.match(/anonymous>:(\d+)/) : null;
  if (lineMatch) {
    var lineNum = parseInt(lineMatch[1]);
    console.log('Around line', lineNum);
    for (var k = Math.max(0, lineNum-5); k < Math.min(result.length, lineNum+5); k++) {
      var m = (k === lineNum-1) ? '>>>' : '   ';
      console.log(m + ' ' + (k+1) + ': ' + result[k].substring(0, 200));
    }
  } else {
    // Fallback: binary search
    var lo = 1, hi = result.length;
    while (lo < hi) {
      var mid = Math.floor((lo + hi) / 2);
      try { new vm.Script(result.slice(0, mid).join('\n') + '\n}'); lo = mid + 1; }
      catch(e2) { hi = mid; }
    }
    console.log('Binary search: error near line', lo);
    for (var k = Math.max(0, lo-5); k < Math.min(result.length, lo+5); k++) {
      var m = (k === lo-1) ? '>>>' : '   ';
      console.log(m + ' ' + (k+1) + ': ' + result[k].substring(0, 200));
    }
  }
}
