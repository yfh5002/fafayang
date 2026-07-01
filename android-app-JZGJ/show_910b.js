var fs = require('fs');
var path = 'd:/XM/android-app-JZGJ/app/build/intermediates/assets/debug/index.html';
var content = fs.readFileSync(path, 'utf8');
var startMarker = '<script>\n  // ====================';
var startIdx = content.indexOf(startMarker);
var endIdx = content.indexOf('</script>', startIdx + 100);
var script = content.substring(startIdx + '<script>'.length, endIdx);
var lines = script.split('\n');

var line910 = lines[909];
console.log("Line 910 last 10 chars:", JSON.stringify(line910.substring(line910.length - 10)));
console.log("Line 910 ends with quote:", line910.charAt(line910.length - 1) === "'");
console.log("Line 910 2nd to last char code:", line910.charCodeAt(line910.length - 2));
console.log("Regex match test:", /=\s*\\?'$/.test(line910));

// Show lines 908-915
for (var i = 907; i < 916; i++) {
  var l = lines[i];
  var endsWithQuote = l.charAt(l.length - 1) === "'";
  var hasAssign = l.indexOf('=') !== -1;
  console.log("Line " + (i+1) + " len=" + l.length + " endsQuote=" + endsWithQuote + " hasAssign=" + hasAssign + ": " + JSON.stringify(l.substring(0, 80)));
}
