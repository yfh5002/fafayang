const fs = require('fs');
const content = fs.readFileSync('d:/XM/android-app-JZGJ/app/src/main/assets/index.html', 'utf8');

const startMarker = '<script>\n  // ====================';
const startIdx = content.indexOf(startMarker);
const endIdx = content.indexOf('</script>', startIdx + 100);
const scriptContent = content.substring(startIdx + '<script>'.length, endIdx);
const scriptLines = scriptContent.split('\n');
const htmlBefore = content.substring(0, startIdx + '<script>'.length);
const lineOffset = htmlBefore.split('\n').length;

console.log('Script starts at HTML line:', lineOffset, 'total lines:', scriptLines.length);

// Skip first 20 lines and try from there with a wrapping function
let lastGoodLine = 19;
for (let i = 20; i <= scriptLines.length; i++) {
  const chunk = scriptLines.slice(0, i).join('\n');
  // Wrap in a function body
  try {
    new Function(chunk + '\n');
    lastGoodLine = i;
  } catch(e) {
    const htmlLine = lineOffset + lastGoodLine;
    console.log('Syntax error near HTML line', htmlLine + 1);
    console.log('Error message:', e.message);
    console.log('\nContext:');
    for (let j = Math.max(0, lastGoodLine - 2); j < Math.min(scriptLines.length, lastGoodLine + 8); j++) {
      console.log((lineOffset + j) + ': ' + scriptLines[j].substring(0, 200));
    }
    process.exit(0);
  }
}
console.log('No syntax error found!');
