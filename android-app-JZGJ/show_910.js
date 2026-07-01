var fs = require('fs');
var path = 'd:/XM/android-app-JZGJ/app/build/intermediates/assets/debug/index.html';
var content = fs.readFileSync(path, 'utf8');
var startMarker = '<script>\n  // ====================';
var startIdx = content.indexOf(startMarker);
var endIdx = content.indexOf('</script>', startIdx + 100);
var script = content.substring(startIdx + '<script>'.length, endIdx);
var lines = script.split('\n');

// Show raw bytes of line 910
var line910 = lines[909];
console.log('Line 910 length:', line910.length);
console.log('Line 910 ends with:', JSON.stringify(line910.substring(line910.length - 10)));
console.log('Line 910 regex match =\\s*\\?\\'\\'?:', !!line910.match(/=\s*\\?'$/));
console.log('Line 910 regex match =\\s*\\'\\'?$', !!line910.match(/=\s*'$/));
console.log('Last char code:', line910.charCodeAt(line910.length - 1));

// Also check lines 908-915
for (var i = 907; i < 915; i++) {
  var l = lines[i];
  var last3 = JSON.stringify(l.substring(l.length - 5));
  console.log('Line ' + (i+1) + ' ends: ' + last3 + ' match: ' + !!l.match(/=\s*\\?'$/));
}

// Check line 1124
console.log('\n--- Line 1124 ---');
var line1124 = lines[1123];
console.log('Line 1124 ends: ' + JSON.stringify(line1124.substring(line1124.length - 10)));
console.log('Last char code:', line1124.charCodeAt(line1124.length - 1));
