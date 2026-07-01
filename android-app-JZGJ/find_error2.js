const fs = require('fs');
const content = fs.readFileSync('d:/XM/android-app-JZGJ/app/src/main/assets/index.html', 'utf8');

// Extract the main script block (the big one)
const startMarker = "<script>\n  // ====================";
const startIdx = content.indexOf(startMarker);
if (startIdx === -1) { console.log('Start marker not found'); process.exit(1); }

// Find the closing </script> after this
const endMarker = '</script>';
const endIdx = content.indexOf(endMarker, startIdx + 100);
if (endIdx === -1) { console.log('End marker not found'); process.exit(1); }

const scriptContent = content.substring(startIdx + '<script>'.length, endIdx);
const scriptLines = scriptContent.split('\n');

// Find the line offset in the full HTML
const htmlBefore = content.substring(0, startIdx + '<script>'.length);
const lineOffset = htmlBefore.split('\n').length;

console.log('Script starts at HTML line:', lineOffset);
console.log('Script line count:', scriptLines.length);

// Find syntax error by binary search
let lastGoodLine = 0;
for (let i = 1; i <= scriptLines.length; i++) {
  const chunk = scriptLines.slice(0, i).join('\n');
  const padded = chunk + '\n}}}}}}}}}}}}}}';
  try {
    new Function(padded);
    lastGoodLine = i;
  } catch(e) {
    const htmlLine = lineOffset + lastGoodLine;
    console.log('Syntax error between HTML lines', htmlLine, 'and', htmlLine + 1);
    console.log('\nContext:');
    for (let j = Math.max(0, lastGoodLine - 2); j < Math.min(scriptLines.length, lastGoodLine + 5); j++) {
      console.log((lineOffset + j) + ': ' + scriptLines[j].substring(0, 200));
    }
    break;
  }
}
