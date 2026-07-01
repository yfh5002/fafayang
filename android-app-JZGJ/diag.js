var fs = require('fs');
var path = require('path');

var srcFile = path.join(__dirname, 'app', 'src', 'main', 'assets', 'index.html');
var debugFile = path.join(__dirname, 'app', 'build', 'intermediates', 'assets', 'debug', 'index.html');

function diagnose(filePath, label) {
  try {
    var c = fs.readFileSync(filePath, 'utf8');
    var lines = c.split('\n');
    console.log('=== ' + label + ' ===');
    console.log('Total lines:', lines.length);
    console.log('Total bytes:', c.length);
    
    // Count backslash-single-quote patterns
    var count1 = 0;
    var count2 = 0;
    var count3 = 0;
    for (var i = 0; i < lines.length; i++) {
      var line = lines[i];
      // \\' (two chars: backslash backslash single-quote)
      var m2 = line.match(/\\\\'/g);
      if (m2) count1 += m2.length;
      // \\' (one backslash single-quote) - but only if not preceded by another backslash
      var m1 = line.match(/(?<!\\)\\'/g);
      if (m1) count2 += m1.length;
    }
    
    // Count total single quotes
    var totalQuotes = (c.match(/'/g) || []).length;
    console.log('Total single quotes:', totalQuotes);
    console.log('Lines with backslash-quote:', count1);
    
    // Find multiline string starts
    console.log('\nPotential multiline string starts:');
    for (var i = 0; i < lines.length; i++) {
      var line = lines[i];
      if (/=\s*'[^']*$/.test(line) || /=\s*\\'[^']*$/.test(line)) {
        if (i + 1 < lines.length && lines[i+1].trim().charAt(0) === '<') {
          console.log('  Line ' + (i+1) + ': ' + line.trim().substring(0, 60));
        }
      }
    }
  } catch(e) {
    console.log('Error reading ' + label + ': ' + e.message);
  }
}

diagnose(srcFile, 'Source file');
console.log('');
diagnose(debugFile, 'Debug build file');

// Compare first 100 bytes
try {
  var src = fs.readFileSync(srcFile, 'utf8');
  var dbg = fs.readFileSync(debugFile, 'utf8');
  console.log('\nFiles identical:', src === dbg);
  if (src !== dbg) {
    console.log('Source size:', src.length, 'Debug size:', dbg.length);
    // Find first difference
    for (var i = 0; i < Math.min(src.length, dbg.length); i++) {
      if (src[i] !== dbg[i]) {
        console.log('First diff at byte', i, ': src=', JSON.stringify(src.substring(i, i+20)), ', dbg=', JSON.stringify(dbg.substring(i, i+20)));
        break;
      }
    }
  }
} catch(e) {
  console.log('Compare error:', e.message);
}
