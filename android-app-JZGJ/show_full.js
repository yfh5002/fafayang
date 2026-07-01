var fs = require('fs');
var path = 'd:/XM/android-app-JZGJ/app/build/intermediates/assets/debug/index.html';
var content = fs.readFileSync(path, 'utf8');
var startMarker = '<script>\n  // ====================';
var startIdx = content.indexOf(startMarker);
var endIdx = content.indexOf('</script>', startIdx + 100);
var script = content.substring(startIdx + '<script>'.length, endIdx);
var lines = script.split('\n');

// Line 910 (script) = line 910 in 0-indexed
console.log("Line 910 full:", JSON.stringify(lines[909]));
console.log("");
console.log("Line 915 full:", JSON.stringify(lines[914]));
console.log("");
console.log("Line 916 full:", JSON.stringify(lines[915]));
console.log("");
console.log("Line 1124 full:", JSON.stringify(lines[1123]));
console.log("");
console.log("Line 1125 full:", JSON.stringify(lines[1124]));
