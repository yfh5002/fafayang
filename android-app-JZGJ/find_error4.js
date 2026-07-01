const fs = require('fs');
const vm = require('vm');
const content = fs.readFileSync('d:/XM/android-app-JZGJ/app/src/main/assets/index.html', 'utf8');

const startMarker = '<script>\n  // ====================';
const startIdx = content.indexOf(startMarker);
const endIdx = content.indexOf('</script>', startIdx + 100);
const scriptContent = content.substring(startIdx + '<script>'.length, endIdx);

// Try to compile and get detailed error
try {
  new vm.Script(scriptContent);
  console.log('No syntax error!');
} catch(e) {
  // Extract line/column from stack trace or message
  console.log('Error:', e.message);
  console.log('Stack:', e.stack);
  
  // Try to parse the column number from error
  // V8 errors usually say something like "...:3:5"
  const m = e.stack.match(/<anonymous>:(\d+):(\d+)/);
  if (m) {
    const scriptLine = parseInt(m[1]);
    const col = parseInt(m[2]);
    const htmlBefore = content.substring(0, startIdx + '<script>'.length);
    const lineOffset = htmlBefore.split('\n').length;
    const htmlLine = lineOffset + scriptLine - 1;
    console.log('\nError at script line', scriptLine, 'column', col);
    console.log('Which is HTML line', htmlLine);
    
    const scriptLines = scriptContent.split('\n');
    const start = Math.max(0, scriptLine - 4);
    const end = Math.min(scriptLines.length, scriptLine + 4);
    console.log('\nContext:');
    for (let j = start; j < end; j++) {
      const marker = (j === scriptLine - 1) ? ' >>> ' : '     ';
      console.log(marker + (lineOffset + j) + ': ' + scriptLines[j].substring(0, 200));
    }
  }
}
