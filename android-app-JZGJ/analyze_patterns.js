var fs = require('fs');
var path = require('path');

var srcFile = path.join(__dirname, 'app', 'build', 'intermediates', 'assets', 'debug', 'index.html');
var c = fs.readFileSync(srcFile, 'utf8');
var lines = c.split('\n');

// Find ALL lines containing \' or \\' in the JS script section
var inScript = false;
var scriptStart = 0;
var jsLines = [];

for (var i = 0; i < lines.length; i++) {
  if (lines[i].indexOf('<script>') !== -1) {
    inScript = true;
    scriptStart = i;
  }
  if (lines[i].indexOf('</script>') !== -1) {
    inScript = false;
  }
  if (inScript && i > scriptStart) {
    jsLines.push({ num: i + 1, text: lines[i] });
  }
}

// Find all lines with backslash-quote patterns
console.log('=== Lines with backslash-quote in JS ===');
var problemLines = [];
for (var j = 0; j < jsLines.length; j++) {
  var line = jsLines[j].text;
  if (line.indexOf("\\'") !== -1 || line.indexOf("\\\\'") !== -1) {
    problemLines.push(jsLines[j]);
  }
}

console.log('Total problem lines:', problemLines.length);
console.log('');

// Categorize them
var categories = {
  createElement: [],
  className: [],
  innerHTML_multiline: [],
  getElementById: [],
  setAttribute: [],
  string_assign: [],
  other: []
};

for (var k = 0; k < problemLines.length; k++) {
  var l = problemLines[k];
  var t = l.text.trim();
  
  if (t.indexOf('createElement') !== -1) {
    categories.createElement.push(l);
  } else if (t.indexOf('className') !== -1) {
    categories.className.push(l);
  } else if (t.indexOf('innerHTML =') !== -1) {
    categories.innerHTML_multiline.push(l);
  } else if (t.indexOf('getElementById') !== -1) {
    categories.getElementById.push(l);
  } else if (t.indexOf('setAttribute') !== -1) {
    categories.setAttribute.push(l);
  } else {
    categories.other.push(l);
  }
}

for (var cat in categories) {
  var items = categories[cat];
  console.log('\n=== ' + cat + ' (' + items.length + ') ===');
  var shown = Math.min(items.length, 5);
  for (var m = 0; m < shown; m++) {
    console.log('  Line ' + items[m].num + ': ' + items[m].text.trim().substring(0, 80));
  }
  if (items.length > 5) {
    console.log('  ... and ' + (items.length - 5) + ' more');
  }
}

// Show multiline string patterns
console.log('\n=== Multiline string patterns (line ending with unescaped quote) ===');
for (var n = 0; n < jsLines.length; n++) {
  var ln = jsLines[n];
  var trimmed = ln.text.trimEnd();
  if (/=\s*'$/.test(trimmed) || /=\s*\\'$/.test(trimmed)) {
    // Check if next line is HTML content
    if (n + 1 < jsLines.length && jsLines[n+1].text.trim().charAt(0) === '<') {
      console.log('  Line ' + jsLines[n].num + ': ' + trimmed.substring(0, 70));
      // Show end of multiline
      for (var p = n + 1; p < Math.min(n + 20, jsLines.length); p++) {
        if (/^\s*';?\s*$/.test(jsLines[p].text) || /^\s*\\';?\s*$/.test(jsLines[p].text)) {
          console.log('    -> ends at line ' + jsLines[p].num + ': ' + jsLines[p].text.trim());
          break;
        }
      }
    }
  }
}
