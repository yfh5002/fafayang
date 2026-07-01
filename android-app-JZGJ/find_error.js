const fs = require('fs');
const content = fs.readFileSync('d:/XM/android-app-JZGJ/app/src/main/assets/index.html', 'utf8');

// Extract the main script block
const scriptRegex = /<script[^>]*>([\s\S]*?)<\/script>/gi;
let match;
let scriptIndex = 0;
let mainScript = null;
while ((match = scriptRegex.exec(content)) !== null) {
  scriptIndex++;
  const scriptContent = match[1].trim();
  if (scriptContent.length > 10000) {
    mainScript = scriptContent;
    break;
  }
}

if (!mainScript) {
  console.log('No main script found');
  process.exit(1);
}

// Binary search for syntax error position
function findError(code) {
  try {
    new Function(code);
    return -1; // no error
  } catch(e) {
    // Try to extract position
    const msg = e.message;
    // Try various position patterns
    const patterns = [
      /position\s+(\d+)/i,
      /column\s+(\d+)/i,
      /line\s+\d+\s+col\s+(\d+)/i,
      /\((\d+):(\d+)\)/
    ];
    for (const pat of patterns) {
      const m = msg.match(pat);
      if (m) return parseInt(m[1]);
    }
    return null;
  }
}

// Try to narrow down the error location
// First, try splitting in half
function binarySearchError(code) {
  // Find approximate line by trying chunks
  const lines = code.split('\n');
  console.log('Total lines in script:', lines.length);
  
  // Try incrementally larger prefixes
  let lastGood = 0;
  for (let i = 1; i <= lines.length; i++) {
    const chunk = lines.slice(0, i).join('\n');
    // Pad with closing braces if needed
    const padded = chunk + '\n}}}}';
    try {
      new Function(padded);
      lastGood = i;
    } catch(e) {
      if (i === 1) {
        console.log('Error on line 1');
      }
      // Print context around the error
      console.log('Error between lines', lastGood, 'and', i);
      console.log('Last good line:', lines[lastGood-1]);
      console.log('Error line:', lines[i-1]);
      console.log('Next line:', i < lines.length ? lines[i] : 'END');
      // Print more context
      const start = Math.max(0, i-3);
      const end = Math.min(lines.length, i+3);
      console.log('\nContext:');
      for (let j = start; j < end; j++) {
        console.log((j+1) + ': ' + lines[j].substring(0, 150));
      }
      return;
    }
  }
  console.log('No error found in prefix search');
}

binarySearchError(mainScript);
