const fs = require('fs');
const c = fs.readFileSync('d:/XM/android-app-JZGJ/app/src/main/assets/index.html', 'utf8');
const lines = c.split('\n');

// Find lines with inconsistent quoting
let issues = 0;
for (let i = 0; i < lines.length; i++) {
  const line = lines[i];
  // Check for problematic patterns
  if (line.includes("= '") && !line.includes("\\'") && !line.includes("='") && line.trim().startsWith('elements') || 
      line.includes("= '") && line.includes('<div') && !line.includes("' +")) {
    console.log('Possible issue at line ' + (i+1) + ': ' + line.substring(0, 120));
    issues++;
  }
}

// Also check for the 4-backslash pattern
for (let i = 0; i < lines.length; i++) {
  if (lines[i].includes('\\\\\\'') || lines[i].includes("\\\\\\\\'")) {
    console.log('4-backslash at line ' + (i+1) + ': ' + lines[i].substring(0, 120));
    issues++;
  }
}

console.log('\nTotal issues found: ' + issues);

// Try to find where the transition happens
let inScript = false;
let scriptStart = 0;
for (let i = 0; i < lines.length; i++) {
  if (lines[i].includes('<script>')) { inScript = true; scriptStart = i; }
  if (lines[i].includes('</script>')) { inScript = false; }
  if (inScript && i > scriptStart + 5) {
    // Check the quoting style
    if (lines[i].match(/innerHTML\s*=\s*'/) && !lines[i].match(/\\'/)) {
      console.log('\nUnescaped innerHTML at line ' + (i+1));
    }
  }
}
