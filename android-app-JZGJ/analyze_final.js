var fs = require('fs');
var vm = require('vm');

var path = 'd:/XM/android-app-JZGJ/app/build/intermediates/assets/debug/index.html';
var content = fs.readFileSync(path, 'utf8');

var startMarker = '<script>\n  // ====================';
var startIdx = content.indexOf(startMarker);
var endIdx = content.indexOf('</script>', startIdx + 100);
var script = content.substring(startIdx + '<script>'.length, endIdx);

// Apply transforms
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

// Find all lines that might have quote issues
for (var k = 0; k < result.length; k++) {
  var l = result[k];
  // Look for lines with unbalanced quotes
  var singleQuotes = (l.match(/'/g) || []).length;
  // If odd number of single quotes, might be problematic
  // (but could also be inside a multi-line context)
  
  // Look for string concatenation with + that has unbalanced quotes
  // Pattern: 'text1' + 'text2' where quotes are unbalanced within concatenation
  
  // More useful: find lines containing HTML attributes with onclick=
  // These often have nested quotes that need escaping
  if (l.indexOf('onclick=') !== -1 || l.indexOf("onclick='") !== -1) {
    // Count single quotes
    var sq = (l.match(/'/g) || []).length;
    if (sq % 2 !== 0) {
      console.log('ODD quotes at line ' + (k+1) + ' (' + sq + ' quotes):');
      console.log('  ' + l.substring(0, 200));
    }
  }
  
  // Also look for lines with "楼" (mojibake for ¥)
  if (l.indexOf('\u697C') !== -1) {
    console.log('MOJIBAKE at line ' + (k+1) + ': ' + l.substring(0, 150));
  }
}

console.log('\n--- Checking for specific problematic patterns ---');

// Look for patterns where HTML attribute values use single quotes inside JS single-quote strings
// e.g.: '<button onclick='editRecord(' + id + ')'>' 
// This is invalid because the onclick= value's quote conflicts with the JS string quote

// Find lines with: onclick=
for (var k = 0; k < result.length; k++) {
  var l = result[k];
  if (l.indexOf("onclick='") !== -1 || l.indexOf('onclick="') !== -1) {
    console.log('\nLine ' + (k+1) + ' with onclick=');
    console.log('  ' + l.substring(0, 250));
  }
}
