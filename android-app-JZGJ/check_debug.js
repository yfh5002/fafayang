var fs = require('fs');
var vm = require('vm');

var path = 'd:/XM/android-app-JZGJ/app/build/intermediates/assets/debug/index.html';
var content = fs.readFileSync(path, 'utf8');
var startMarker = '<script>\n  // ====================';
var startIdx = content.indexOf(startMarker);
var endIdx = content.indexOf('</script>', startIdx + 100);
var script = content.substring(startIdx + '<script>'.length, endIdx);

var lines = script.split('\n');

// Check specific lines around the known error
for (var i = 895; i < 910; i++) {
  console.log((i+1) + ': ' + JSON.stringify(lines[i]).substring(0, 150));
}

// Find multi-line string starts
console.log('\n--- Multi-line string starts ---');
for (var i = 0; i < lines.length; i++) {
  if (lines[i].match(/=\s*'$/) && !lines[i].match(/\\'/)) {
    console.log('Line ' + (i+1) + ': ' + lines[i].substring(0, 100));
  }
}
