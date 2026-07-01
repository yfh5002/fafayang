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

console.log('Step 0: Original length', script.length);

// Step 1: Fix multi-line strings FIRST (before any quote replacement)
// We need to handle them in their original form

var lines = script.split('\n');
var result = [];
var i = 0;
var multiLineCount = 0;

while (i < lines.length) {
  var line = lines[i];
  
  // Check if this line ends with = ' or += ' (opening a multi-line single-quote string)
  if (line.match(/=\s*'$/) || line.match(/\+=\s*'$/)) {
    var collected = [line];
    var j = i + 1;
    var found = false;
    while (j < lines.length) {
      collected.push(lines[j]);
      // The end of multi-line string could be:
      // - ';  (plain)
      // - \\'; (with escaped quote)
      // - \' (just escaped quote)
      if (lines[j].match(/^\s*';\s*$/) || lines[j].match(/^\s*\\';\s*$/) || lines[j].match(/^\s*\\'\s*$/)) {
        found = true;
        break;
      }
      j++;
    }
    
    if (found && collected.length > 2) {
      multiLineCount++;
      var firstLine = collected[0];
      var lastQuoteIdx = firstLine.lastIndexOf("'");
      var assignment = firstLine.substring(0, lastQuoteIdx);
      
      // Get middle content
      var contentLines = collected.slice(1, -1);
      var joined = contentLines.map(function(l) { return l.trim(); }).join(' ');
      
      // Get the last line and clean up its ending
      var lastLine = collected[collected.length - 1];
      // Remove the closing quote pattern
      var cleanEnd = lastLine.replace(/^\s*/, '').replace(/\\?\s*';?\s*$/, '').replace(/\\'\s*$/, '');
      
      result.push(assignment + "'" + joined + " " + cleanEnd + "';");
      i = j + 1;
    } else {
      result.push(line);
      i++;
    }
  } else {
    result.push(line);
    i++;
  }
}

console.log('Fixed', multiLineCount, 'multi-line strings');

var script2 = result.join('\n');

// Step 2: Replace \\\\' with \'
var before2 = script2.length;
script2 = script2.replace(/\\\\'/g, "\\'");
console.log('Step 2: Replaced \\\\\\\\ with \\\\, length', before2, '->', script2.length);

// Step 3: Replace specific patterns where \' should be '
// createElement(\'x\') -> createElement('x')
script2 = script2.replace(/createElement\(\\'([^)]*?)\\'\)/g, "createElement('$1')");

// .className = \'...\'; -> .className = '...';
script2 = script2.replace(/className = \\'([^]*?)\\';/g, "className = '$1';");

// .value = \'...\'; -> .value = '...';  
script2 = script2.replace(/\.value = \\'([^]*?)\\';/g, ".value = '$1';");

// .textContent = \'...\'; -> .textContent = '...';
script2 = script2.replace(/\.textContent = \\'([^]*?)\\';/g, ".textContent = '$1';");

// style.display = \'...\'; -> style.display = '...';
script2 = script2.replace(/style\.display = \\'([^]*?)\\';/g, "style.display = '$1';");

// .style.display = \'...\'; -> .style.display = '...';
script2 = script2.replace(/\.style\.display = \\'([^]*?)\\';/g, ".style.display = '$1';");

// var x = \'...\'; -> var x = '...';
script2 = script2.replace(/var\s+(\w+)\s*=\s*\\'([^]*?)\\';/g, "var $1 = '$2';");
script2 = script2.replace(/var\s+(\w+)\s*=\s*\\'([^]*?)\\',/g, "var $1 = '$2',");

// || \'...\'; -> || '...';
script2 = script2.replace(/\|\|\s*\\'([^]*?)\\'/g, "|| '$1'");

// titleEl.textContent = \'...\'; -> titleEl.textContent = '...';
script2 = script2.replace(/titleEl\.textContent = \\'([^]*?)\\';/g, "titleEl.textContent = '$1';");

// Step 4: Now fix remaining \' that are used as string delimiters (not inside strings)
// These are tricky. Let's try: replace \'value\' patterns that appear to be standalone string literals
// Pattern: \'word\' where word doesn't contain spaces or special chars
// But this is fragile. Let's try a different approach.

// Actually, let's look at what's left and decide
var remainingEscaped = script2.match(/\\'/g);
console.log('Remaining escaped quotes:', remainingEscaped ? remainingEscaped.length : 0);

// Show first 20 occurrences
if (remainingEscaped) {
  var lines2 = script2.split('\n');
  var count = 0;
  for (var k = 0; k < lines2.length && count < 20; k++) {
    if (lines2[k].indexOf("\\'") !== -1) {
      console.log('  Line ' + (k+1) + ': ' + lines2[k].substring(0, 150));
      count++;
    }
  }
}

// Try to compile
try {
  new vm.Script(script2);
  console.log('\nSUCCESS!');
  var newContent = prefix + script2 + '\n' + suffix;
  fs.writeFileSync('d:/XM/android-app-JZGJ/app/src/main/assets/index.html', newContent, 'utf8');
  console.log('File saved.');
} catch(e) {
  console.log('\nERROR:', e.message);
  var lo = 1, hi = script2.split('\n').length;
  var lines2 = script2.split('\n');
  while (lo < hi) {
    var mid = Math.floor((lo + hi) / 2);
    try { new vm.Script(lines2.slice(0, mid).join('\n') + '\n}'); lo = mid + 1; }
    catch(e2) { hi = mid; }
  }
  console.log('Error near line', lo);
  for (var k = Math.max(0, lo-5); k < Math.min(lines2.length, lo+5); k++) {
    var m = (k === lo-1) ? '>>>' : '   ';
    console.log(m + ' ' + (k+1) + ': ' + lines2[k].substring(0, 250));
  }
}
