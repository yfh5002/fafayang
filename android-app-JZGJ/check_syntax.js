const fs = require('fs');
const content = fs.readFileSync('d:/XM/android-app-JZGJ/app/src/main/assets/index.html', 'utf8');

// Extract all script blocks
const scriptRegex = /<script[^>]*>([\s\S]*?)<\/script>/gi;
let match;
let scriptIndex = 0;
while ((match = scriptRegex.exec(content)) !== null) {
  scriptIndex++;
  const scriptContent = match[1].trim();
  if (scriptContent.length > 10) {
    console.log(`\n=== Script block ${scriptIndex} (starts at char ${match.index}, length ${scriptContent.length}) ===`);
    console.log('First 200 chars:', scriptContent.substring(0, 200));
    
    // Try to parse with Function constructor to find syntax errors
    try {
      new Function(scriptContent);
      console.log('SYNTAX OK');
    } catch(e) {
      console.log('SYNTAX ERROR:', e.message);
      // Try to find approximate line
      const match2 = e.message.match(/position\s+(\d+)/i);
      if (match2) {
        const pos = parseInt(match2[1]);
        const before = scriptContent.substring(0, pos);
        const line = before.split('\n').length;
        console.log('Approximate error line (relative to script start):', line);
        console.log('Context:', scriptContent.substring(Math.max(0, pos-100), pos+50));
      }
    }
  }
}
