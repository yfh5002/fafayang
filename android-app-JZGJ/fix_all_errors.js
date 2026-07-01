const fs = require('fs');
const vm = require('vm');

const filePath = 'd:/XM/android-app-JZGJ/app/src/main/assets/index.html';
let content = fs.readFileSync(filePath, 'utf8');

// Find the main script block boundaries
const startMarker = '<script>\n  // ====================';
const startIdx = content.indexOf(startMarker);
const scriptTagStart = content.lastIndexOf('<script>', startIdx);
const endIdx = content.indexOf('</script>', startIdx + 100);

const beforeScript = content.substring(0, scriptTagStart);
const afterScript = content.substring(endIdx + '</script>'.length);
let script = content.substring(scriptTagStart + '<script>'.length, endIdx);

console.log('Original script length:', script.length);

// Fix 1: Replace \\' (double backslash + quote) with just ' in JavaScript code
// These are actual chars: \ \ ' (char codes 92 92 39)
// They appear in JS code where just ' (char code 39) is needed
let fix1Count = 0;
script = script.replace(/\\\\'/g, function() {
  fix1Count++;
  return "'";
});
console.log('Fix 1 (\\\\\' -> \'): replaced', fix1Count, 'occurrences');

// Fix 2: Replace \' (single backslash + quote) with just ' when used as string delimiters
// In JavaScript, \' inside a single-quoted string is an escaped quote
// But outside a string, \' is a line continuation which causes issues
// We need to be careful: inside strings, \' is valid; outside strings, it's usually wrong
// For now, let's check if there are any remaining \' that are problematic

// Fix 3: Handle multi-line single-quoted strings (lines with just ' at the end, followed by HTML, then \';)
// These need to be converted to string concatenation
let fix3Count = 0;

const lines = script.split('\n');
const result = [];
let i = 0;
let inMultiLineString = false;
let stringStartIndent = '';

while (i < lines.length) {
  const line = lines[i];
  
  if (!inMultiLineString) {
    // Check if this line starts a multi-line string (ends with just ' at the line end)
    // Pattern: something = '\n or something + '\n
    if (/['"]\s*$/.test(line.trim()) && !line.trim().endsWith("';") && !line.trim().endsWith('";')) {
      // Check if this looks like a string assignment
      const trimmed = line.trim();
      if (trimmed.endsWith("'") || trimmed.endsWith('"')) {
        // This might be the start of a multi-line string
        // Look ahead to see if there's content on next lines before the closing quote
        if (i + 1 < lines.length) {
          const nextLine = lines[i + 1].trim();
          if (nextLine.startsWith('<') || nextLine.length > 0) {
            // This is likely a multi-line string
            inMultiLineString = true;
            stringStartIndent = line.match(/^(\s*)/)[1];
            const quoteChar = trimmed.endsWith("'") ? "'" : '"';
            const assignment = trimmed.slice(0, -1); // remove trailing quote
            result.push(stringStartIndent + assignment + ' ' + quoteChar);
            result.push(lines[i + 1]); // add the HTML content line
            i += 2;
            continue;
          }
        }
      }
    }
    result.push(line);
    i++;
  } else {
    // We're inside a multi-line string
    const trimmed = line.trim();
    if (trimmed === "\\';" || trimmed === "';" || trimmed === '\\";' || trimmed === '";') {
      // End of multi-line string
      // The line is just \'; or ';  - it closes the string
      // We need to add + ' before the last HTML line and close with ';
      // Actually, we already added the opening quote, and the lines in between are HTML content
      // We just need to close it properly
      // Find the last result line that has HTML content
      if (trimmed === "\\';") {
        result.push(stringStartIndent + "';");
      } else {
        result.push(stringStartIndent + trimmed);
      }
      inMultiLineString = false;
      fix3Count++;
    } else {
      result.push(line);
    }
    i++;
  }
}

script = result.join('\n');
console.log('Fix 3 (multi-line strings): fixed', fix3Count, 'occurrences');

// Now reassemble the file
content = beforeScript + '<script>' + script + '</script>' + afterScript;

// Save the fixed file
fs.writeFileSync(filePath, content, 'utf8');
console.log('File saved.');

// Verify: try to parse the script
try {
  new vm.Script(script);
  console.log('\nSYNTAX CHECK: PASSED - No syntax errors found!');
} catch(e) {
  console.log('\nSYNTAX CHECK: FAILED - Still has errors');
  console.log('Error:', e.message);
  
  const m = e.stack.match(/<anonymous>:(\d+):(\d+)/);
  if (m) {
    const scriptLine = parseInt(m[1]);
    const scriptLines = script.split('\n');
    const start = Math.max(0, scriptLine - 3);
    const end = Math.min(scriptLines.length, scriptLine + 3);
    console.log('\nContext:');
    for (let j = start; j < end; j++) {
      const marker = (j === scriptLine - 1) ? ' >>> ' : '     ';
      console.log(marker + (j+1) + ': ' + scriptLines[j].substring(0, 200));
    }
  }
}
