const fs = require('fs');
const vm = require('vm');

let content = fs.readFileSync('d:/XM/android-app-JZGJ/app/src/main/assets/index.html', 'utf8');

const startMarker = '<script>\n  // ====================';
const startIdx = content.indexOf(startMarker);
const endIdx = content.indexOf('</script>', startIdx + 100);
const scriptPrefix = content.substring(0, startIdx + '<script>'.length);
const scriptSuffix = content.substring(endIdx);
let script = content.substring(startIdx + '<script>'.length, endIdx);

// The core issue: there are multi-line string assignments using single quotes
// like:  xxx.innerHTML = '\n  <div ...>\n...\n';
// This is invalid JS. Single-quoted strings can't span lines.
// 
// Also there are escaped quotes like: \'value\'  (single backslash)
// and double-escaped: \\\'value\\\' (double backslash = literal \' in source)
// and quadruple-escaped: \\\\'value\\\\' (in file = \\', in JS = \' = just a quote)
//
// Strategy: Convert ALL multi-line single-quoted strings to use string concatenation.

let lines = script.split('\n');
let result = [];
let i = 0;

function isInsideMultiLineString(line) {
  // Detect patterns like: xxx.innerHTML = ' or xxx = '
  // where the string starts on this line but doesn't end
  const trimmed = line.trimEnd();
  // Check for assignment with opening quote but no closing quote on same line
  // Pattern: = ' (at end of line) without matching ';
  const match = trimmed.match(/=\s*'$/);
  return !!match;
}

function fixEscapedQuotes(str) {
  // Replace \\\\' with ' (four backslashes + quote -> just quote)
  // In the file: \\ means literal backslash, so \\\\' = literal \' which in JS source = just '
  // But we want actual string quotes, so replace with '
  str = str.replace(/\\\\'/g, "'");
  
  // Replace \\\' with ' (three backslashes + quote -> quote)
  // In file: \' = escaped quote in JS = just ' in the string
  str = str.replace(/\\\'/g, "'");
  
  // Replace \' with ' (single backslash + quote -> quote in normal context)
  // But be careful: inside a string we DO need \' to escape quotes
  // We need context-aware replacement
  
  return str;
}

while (i < lines.length) {
  let line = lines[i];
  
  // Check if this line starts a multi-line string
  // Look for: something = ' at end of line (without closing quote)
  if (isInsideMultiLineString(line)) {
    // This starts a multi-line string. Collect all lines until we find the closing ';
    let multiLine = [line];
    let j = i + 1;
    
    // Find the end of the multi-line string
    // The closing pattern is something like: \\'; or '; at start of line
    let found = false;
    while (j < lines.length) {
      multiLine.push(lines[j]);
      // Check if this line ends the string
      // Look for '; at the beginning (with optional whitespace)  
      if (/^\s*'/.test(lines[j]) || /^\s*\\';/.test(lines[j])) {
        found = true;
        break;
      }
      j++;
    }
    
    if (!found) {
      // Couldn't find end - keep as-is
      result.push(line);
      i++;
      continue;
    }
    
    // Now we have the full multi-line string from lines[i] to lines[j]
    // Convert it to a single-line string
    // Remove the opening = ' from the first line
    let firstLine = multiLine[0];
    let prefix = firstLine.substring(0, firstLine.lastIndexOf("'") + 1).replace(/=\s*'$/, '= \'');
    // Actually, let's just join all the middle lines and handle quotes properly
    
    // Extract the content parts
    let content_lines = multiLine.slice(1, -1); // middle lines (without first and last)
    let lastLine = multiLine[multiLine.length - 1];
    
    // Process: join all content lines, fix quotes, make it a proper single-line string
    let joinedContent = content_lines.join(' ');
    
    // Fix the escaped quotes in the content
    // Replace \\\\' with ' 
    joinedContent = joinedContent.replace(/\\\\'/g, "'");
    // Replace \\\' with '
    joinedContent = joinedContent.replace(/\\\'/g, "'");
    // Replace \' with ' (for values inside the string that use string concatenation)
    // We need to be more careful here...
    
    // Fix the closing: \\'; -> ';
    let closingFixed = lastLine.replace(/^\s*\\'/, "'").replace(/^\s*'/, "'");
    
    // Build the single-line version
    // The first line has the assignment like: xxx.innerHTML = '
    // We keep that, add the content as one line, then the closing ';
    let assignment = firstLine.replace(/=\s*'$/, "= '");
    let fullLine = assignment + joinedContent + ' ' + closingFixed.trim();
    
    // But this might be too long. Let's use string concatenation with +
    // For now, just output it as one line
    result.push(fullLine);
    i = j + 1;
  } else {
    // Fix escaped quotes in normal lines
    // Replace \\\\' with '
    line = line.replace(/\\\\'/g, "'");
    // Replace \\\' with ' 
    line = line.replace(/\\\'/g, "'");
    result.push(line);
    i++;
  }
}

let newScript = result.join('\n');

// Verify
try {
  new vm.Script(newScript);
  console.log('SUCCESS: Script compiles without errors!');
  
  // Write back
  const newContent = scriptPrefix + newScript + '\n' + scriptSuffix;
  fs.writeFileSync('d:/XM/android-app-JZGJ/app/src/main/assets/index.html', newContent, 'utf8');
  console.log('File saved successfully.');
} catch(e) {
  console.log('ERROR:', e.message);
  const m = e.stack.match(/<anonymous>:(\d+):(\d+)/);
  if (m) {
    const scriptLine = parseInt(m[1]);
    const start2 = Math.max(0, scriptLine - 5);
    const end2 = Math.min(result.length, scriptLine + 5);
    for (let j = start2; j < end2; j++) {
      const marker = (j === scriptLine - 1) ? '>>>' : '   ';
      console.log(marker + ' ' + (j+1) + ': ' + result[j].substring(0, 200));
    }
  }
  // Don't save if there's still an error
  console.log('File NOT saved due to remaining errors.');
}
