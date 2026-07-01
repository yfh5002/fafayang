var fs = require('fs');
var path = 'd:/XM/android-app-JZGJ/app/build/intermediates/assets/debug/index.html';
var content = fs.readFileSync(path, 'utf8');
var startMarker = '<script>\n  // ====================';
var startIdx = content.indexOf(startMarker);
var endIdx = content.indexOf('</script>', startIdx + 100);
var script = content.substring(startIdx + '<script>'.length, endIdx);
var lines = script.split('\n');

// Find lines ending with = ' or \'
for (var i = 0; i < lines.length; i++) {
  if (lines[i].match(/=\s*'[^']*$/) || lines[i].match(/=\s*\\'[^']*$/)) {
    console.log((i+1) + ': ' + lines[i].substring(0, 150));
  }
}

// Also show lines around 816 (where the error was reported)
console.log('\n--- Around line 816 ---');
for (var i = 810; i < 830; i++) {
  console.log((i+1) + ': ' + lines[i].substring(0, 200));
}

// Show line with innerHTML
console.log('\n--- innerHTML lines ---');
for (var i = 0; i < lines.length; i++) {
  if (lines[i].indexOf('innerHTML =') !== -1 && lines[i].match(/= *'[^']*$/)) {
    console.log((i+1) + ': ' + lines[i].substring(0, 150));
  }
}

// Show the getAccountName function
console.log('\n--- getAccountName ---');
for (var i = 0; i < lines.length; i++) {
  if (lines[i].indexOf('getAccountName') !== -1) {
    console.log((i+1) + ': ' + lines[i].substring(0, 200));
  }
}
