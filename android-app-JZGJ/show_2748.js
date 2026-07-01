var fs = require('fs');
var path = 'd:/XM/android-app-JZGJ/app/build/intermediates/assets/debug/index.html';
var content = fs.readFileSync(path, 'utf8');
var startMarker = '<script>\n  // ====================';
var startIdx = content.indexOf(startMarker);
var endIdx = content.indexOf('</script>', startIdx + 100);
var script = content.substring(startIdx + '<script>'.length, endIdx);
var lines = script.split('\n');

// Show lines 2745-2765
for (var i = 2744; i < 2765; i++) {
  console.log((i+1) + ': ' + JSON.stringify(lines[i]).substring(0, 200));
}
