const fs = require('fs');
const vm = require('vm');

let content = fs.readFileSync('d:/XM/android-app-JZGJ/app/src/main/assets/index.html', 'utf8');

const startMarker = '<script>\n  // ====================';
const startIdx = content.indexOf(startMarker);
const endIdx = content.indexOf('</script>', startIdx + 100);
let scriptContent = content.substring(startIdx + '<script>'.length, endIdx);

try {
  new vm.Script(scriptContent);
  console.log('SUCCESS: No syntax errors!');
  process.exit(0);
} catch(e) {
  console.log('Error:', e.message);
  // Parse the stack to find the line
  const stackLines = e.stack.split('\n');
  for (const line of stackLines) {
    const m = line.match(/<anonymous>:(\d+):(\d+)/);
    if (m) {
      const scriptLine = parseInt(m[1]);
      const col = parseInt(m[2]);
      const scriptLines = scriptContent.split('\n');
      console.log('\nScript line', scriptLine, 'column', col);
      const start = Math.max(0, scriptLine - 6);
      const end = Math.min(scriptLines.length, scriptLine + 6);
      for (let j = start; j < end; j++) {
        const marker = (j === scriptLine - 1) ? '>>>' : '   ';
        console.log(marker + ' ' + (j+1) + ': ' + scriptLines[j]);
      }
      break;
    }
  }
}
