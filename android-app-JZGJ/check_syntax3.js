const fs = require('fs');
const vm = require('vm');

let content = fs.readFileSync('d:/XM/android-app-JZGJ/app/src/main/assets/index.html', 'utf8');

const startMarker = '<script>\n  // ====================';
const startIdx = content.indexOf(startMarker);
const endIdx = content.indexOf('</script>', startIdx + 100);
let scriptContent = content.substring(startIdx + '<script>'.length, endIdx);

const lines = scriptContent.split('\n');
console.log('Total lines:', lines.length);

// Binary search for the error line
let lo = 1, hi = lines.length;
while (lo < hi) {
  let mid = Math.floor((lo + hi) / 2);
  let partial = lines.slice(0, mid).join('\n');
  try {
    // Wrap in a function so incomplete code doesn't throw "unexpected end of input"
    // We use eval approach: try to parse what we have
    new vm.Script(partial + '\n}); // close any open blocks');
    lo = mid + 1;
  } catch(e) {
    if (e.message.includes('Invalid or unexpected token') || e.message.includes('Unexpected token')) {
      hi = mid;
    } else {
      // Other errors (like missing closing brace) - error is before here
      hi = mid;
    }
  }
}

console.log('Error is around line', lo);
for (let i = Math.max(0, lo-5); i < Math.min(lines.length, lo+5); i++) {
  const marker = (i === lo-1) ? '>>>' : '   ';
  console.log(marker + ' ' + (i+1) + ': ' + lines[i]);
}
