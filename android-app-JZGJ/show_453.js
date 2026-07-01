var fs = require('fs');
var vm = require('vm');

var path = 'd:/XM/android-app-JZGJ/app/build/intermediates/assets/debug/index.html';
var content = fs.readFileSync(path, 'utf8');

var startMarker = '<script>\n  // ====================';
var startIdx = content.indexOf(startMarker);
var endIdx = content.indexOf('</script>', startIdx + 100);
var script = content.substring(startIdx + '<script>'.length, endIdx);

// Apply the same transforms as fix_complete3.js
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
      if (lines[j].match(/^\s*';\s*$/) || lines[j].match(/^\s*\\';\s*$/) || lines[j].match(/^\s*'\s*$/)) { found = true; break; }
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

// Fix onclick patterns
var sLines = s.split('\n');
for (var k = 0; k < sLines.length; k++) {
  var l = sLines[k];
  if (l.indexOf('onclick="') !== -1) {
    var pos = 0;
    var lineResult = '';
    var len = l.length;
    while (pos < len) {
      if (l.substring(pos).indexOf('onclick="') === 0) {
        lineResult += 'onclick="';
        pos += 9;
        while (pos < len) {
          var ch = l[pos];
          if (ch === '"') {
            lineResult += '"';
            pos++;
            break;
          } else if (ch === "'") {
            lineResult += "\\'";
            pos++;
          } else {
            lineResult += ch;
            pos++;
          }
        }
      } else {
        lineResult += l[pos];
        pos++;
      }
    }
    sLines[k] = lineResult;
  }
}
s = sLines.join('\n');

// Show lines 440-460
var sLines2 = s.split('\n');
for (var k = 440; k < 460; k++) {
  console.log((k+1) + ': ' + sLines2[k].substring(0, 250));
}
