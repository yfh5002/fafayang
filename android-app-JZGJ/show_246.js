var fs = require('fs');
var vm = require('vm');

var path = 'd:/XM/android-app-JZGJ/app/build/intermediates/assets/debug/index.html';
var content = fs.readFileSync(path, 'utf8');

var startMarker = '<script>\n  // ====================';
var startIdx = content.indexOf(startMarker);
var endIdx = content.indexOf('</script>', startIdx + 100);
var script = content.substring(startIdx + '<script>'.length, endIdx);

// Apply same transforms as fix_complete2.js
var lines = script.split('\n');
var result = [];
var i = 0;
while (i < lines.length) {
  var line = lines[i];
  if (line.match(/=\s*\\?'$/) || line.match(/\+=\s*\\?'$/) || line.match(/return\s*\\?'$/)) {
    var collected = [line];
    var j = i + 1;
    var found = false;
    while (j < lines.length) {
      collected.push(lines[j]);
      if (lines[j].match(/^\s*';\s*$/) || lines[j].match(/^\s*\\';\s*$/) || lines[j].match(/^\s*'\s*$/)) {
        found = true;
        break;
      }
      j++;
    }
    if (found && collected.length > 2) {
      var firstLine = collected[0];
      var lastQuoteIdx = firstLine.lastIndexOf("'");
      var assignment = firstLine.substring(0, lastQuoteIdx);
      var contentLines = collected.slice(1, -1);
      var lastLine = collected[collected.length - 1];
      var lastClean = lastLine.replace(/^\s*/, '').replace(/\\?\s*';?\s*$/, '');
      var allContent = contentLines.map(function(l) { return l.trim(); }).join(' ') + ' ' + lastClean;
      allContent = allContent.replace(/\s+/g, ' ').trim();
      result.push(assignment + "'" + allContent + "';");
      i = j + 1;
    } else { result.push(line); i++; }
  } else { result.push(line); i++; }
}

var s = result.join('\n');
s = s.replace(/\\\\'/g, "'");
s = s.replace(/\\'/g, "'");

var sLines = s.split('\n');
// Show lines 244-260
for (var k = 243; k < 260; k++) {
  console.log((k+1) + ': ' + sLines[k].substring(0, 250));
}
