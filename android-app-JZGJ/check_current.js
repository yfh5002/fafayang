var fs = require('fs');
var vm = require('vm');

var content = fs.readFileSync('d:/XM/android-app-JZGJ/app/src/main/assets/index.html', 'utf8');

var startMarker = '<script>\n  // ====================';
var startIdx = content.indexOf(startMarker);
var endIdx = content.indexOf('</script>', startIdx + 100);
var script = content.substring(startIdx + '<script>'.length, endIdx);

var lines = script.split('\n');

// Find lines with problematic patterns
for (var i = 0; i < lines.length; i++) {
  // Look for = ' at end (potential multi-line string start)
  if (lines[i].match(/=\s*'$/)) {
    console.log('Possible multi-line start at script line ' + (i+1) + ': ' + JSON.stringify(lines[i]).substring(0, 100));
  }
  // Look for \'; at start (potential multi-line string end)
  if (lines[i].match(/^\s*\\'/)) {
    console.log('Possible multi-line end at script line ' + (i+1) + ': ' + JSON.stringify(lines[i]).substring(0, 100));
  }
  // Look for standalone \' (escaped quote outside string)
  if (lines[i].match(/[^'"]\\'/)) {
    console.log('Escaped quote at script line ' + (i+1) + ': ' + JSON.stringify(lines[i]).substring(0, 150));
  }
}

// Try to compile
try {
  new vm.Script(script);
  console.log('\nSUCCESS');
} catch(e) {
  console.log('\nERROR:', e.message);
  var stackLines = e.stack.split('\n');
  for (var j = 0; j < stackLines.length; j++) {
    var m = stackLines[j].match(/<anonymous>:(\d+):(\d+)/);
    if (m) {
      var lineNum = parseInt(m[1]);
      console.log('At script line', lineNum);
      for (var k = Math.max(0, lineNum - 4); k < Math.min(lines.length, lineNum + 4); k++) {
        var marker = (k === lineNum - 1) ? '>>>' : '   ';
        console.log(marker + ' ' + (k+1) + ': ' + lines[k].substring(0, 200));
      }
      break;
    }
  }
}
