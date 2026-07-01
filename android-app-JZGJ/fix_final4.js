var fs = require('fs');
var vm = require('vm');

var path = 'd:/XM/android-app-JZGJ/app/build/intermediates/assets/debug/index.html';
var content = fs.readFileSync(path, 'utf8');

var startMarker = '<script>\n  // ====================';
var startIdx = content.indexOf(startMarker);
var endIdx = content.indexOf('</script>', startIdx + 100);
var prefix = content.substring(0, startIdx + '<script>'.length);
var suffix = content.substring(endIdx);
var script = content.substring(startIdx + '<script>'.length, endIdx);

// Strategy: 
// Replace \\\\' (4 backslash chars) with \' (escaped quote in JS = literal ' in string)
// Replace \\' (2 backslash chars) with \' (escaped quote in JS)
// But we can't blindly do this because some \\' should just be '
//
// Actually, let's think about what the INTENDED code should be:
// 
// 1. document.createElement(\\\\'div\\\\') should be document.createElement('div')
//    Here \\\\' is file bytes \\ + ', which in JS is \' (escaped quote) 
//    But we want just ' here (plain quote)
//    
// 2. '<div onclick="selectBackupPath(\\\\' + opt.path + '\\\\')">'
//    should be: '<div onclick="selectBackupPath(\'' + opt.path + '\'")">'
//    Here \\\\' should become \' (escaped quote inside JS string)
//
// So the rule is:
// - When \\\\' appears OUTSIDE a JS string, replace with '
// - When \\\\' appears INSIDE a JS string, replace with \'
//
// We can approximate this by:
// 1. First, identify string regions
// 2. Apply different replacements inside vs outside strings
//
// But parsing strings is complex. Let me try a simpler approach:
// - In file: \\\\' should become \' everywhere
// - Then, for patterns like createElement(\'div\'), replace \' with '
// - For patterns inside HTML strings (onclick=), keep \'

// Actually, the simplest fix: 
// Replace \\\\' with \' everywhere
// Then replace specific known-bad patterns

// Step 1: \\\\' -> \'
script = script.replace(/\\\\'/g, "\\'");

// Step 2: \\' -> ' (for cases where \' is used outside strings like createElement)
// But only for specific patterns we know are wrong
// createElement(\'div\') -> createElement('div')
script = script.replace(/createElement\(\\'([^)]*?)\\'\)/g, "createElement('$1')");
// className = \'...\'; -> className = '...';
script = script.replace(/className = \\'([^]*?)\\';/g, "className = '$1';");
// style.display = \'...\'; -> style.display = '...';
script = script.replace(/style\.display = \\'([^]*?)\\';/g, "style.display = '$1';");
// .value = \'...\'; -> .value = '...';
script = script.replace(/\.value = \\'([^]*?)\\';/g, ".value = '$1';");
// .textContent = \'...\'; -> .textContent = '...';
script = script.replace(/\.textContent = \\'([^]*?)\\';/g, ".textContent = '$1';");

// Variable declarations: var x = \'...\'; -> var x = '...';
script = script.replace(/var\s+(\w+)\s*=\s*\\'([^]*?)\\';/g, "var $1 = '$2';");
script = script.replace(/var\s+(\w+)\s*=\s*\\'([^]*?)\\',/g, "var $1 = '$2',");

// Simple string comparisons: === \'value\' -> === 'value'
// But only when NOT inside another string (hard to detect)
// Let's skip this for now and see if it compiles

// Step 3: Fix multi-line strings
var lines = script.split('\n');
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
      var contentLines = collected.slice(1, -1);
      var joined = contentLines.map(function(l) { return l.trim(); }).join(' ');
      result.push(assignment + "'" + joined + "';");
      i = j + 1;
    } else { result.push(line); i++; }
  } else { result.push(line); i++; }
}

var newScript = result.join('\n');

try {
  new vm.Script(newScript);
  console.log('SUCCESS!');
  var newContent = prefix + newScript + '\n' + suffix;
  fs.writeFileSync('d:/XM/android-app-JZGJ/app/src/main/assets/index.html', newContent, 'utf8');
  console.log('File saved. Lines: ' + lines.length + ' -> ' + result.length);
} catch(e) {
  console.log('ERROR:', e.message);
  var lo = 1, hi = result.length;
  while (lo < hi) {
    var mid = Math.floor((lo + hi) / 2);
    try { new vm.Script(result.slice(0, mid).join('\n') + '\n}'); lo = mid + 1; }
    catch(e2) { hi = mid; }
  }
  console.log('Error near line', lo);
  for (var k = Math.max(0, lo-5); k < Math.min(result.length, lo+5); k++) {
    var m = (k === lo-1) ? '>>>' : '   ';
    console.log(m + ' ' + (k+1) + ': ' + result[k].substring(0, 200));
  }
}
