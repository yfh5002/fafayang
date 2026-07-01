// Fix quoting issues in index.html
const fs = require('fs');
const vm = require('vm');

let content = fs.readFileSync('d:/XM/android-app-JZGJ/app/src/main/assets/index.html', 'utf8');

// Extract the main script block
const startMarker = '<script>\n  // ====================';
const startIdx = content.indexOf(startMarker);
const endIdx = content.indexOf('</script>', startIdx + 100);
let scriptContent = content.substring(startIdx + '<script>'.length, endIdx);

console.log('Script length:', scriptContent.length);

// Fix 1: The renderRecentTransactions innerHTML issue
// Line 2612: elements.recentTransactions.innerHTML = '  (raw single quote, should be backtick or escaped)
// Line 2617: \'; should be ';
// We need to replace this specific block

// Fix the empty state innerHTML (lines 2612-2617)
scriptContent = scriptContent.replace(
  /elements\.recentTransactions\.innerHTML = '\s*\n\s*<div class="text-center py-6 text-gray-500">\s*\n\s*<i class="fa fa-info-circle text-2xl mb-2"><\/i>\s*\n\s*<p>.*?<\/p>\s*\n\s*<\/div>\s*\n\s*\\';/,
  `elements.recentTransactions.innerHTML = '<div class=\"text-center py-6 text-gray-500\"><i class=\"fa fa-info-circle text-2xl mb-2\"></i><p>暂无交易记录</p></div>';`
);

// Now fix all \\\\' patterns (4 backslash + quote) -> should be single quote or escaped quote
// These are likely from double-escaping. In the actual JS in HTML, we want normal single quotes
// In the file on disk: \\\\'  means the literal characters \\' which in JS source is an escaped single quote = '
// But that's wrong for createElement('div') - we just want createElement('div')

// Let's fix createElement patterns
scriptContent = scriptContent.replace(/document\.createElement\(\\\\\\'([^)]+)\\\\\\'\)/g, 
  "document.createElement('$1')");

// Fix className assignments with \\\\'...\\\\'
scriptContent = scriptContent.replace(/\.className = \\\\'([^)]*?)\\\\';/g, 
  ".className = '$1';");

// Fix innerHTML assignments  
// Pattern: .innerHTML = \\\\'..content..\\\\';
scriptContent = scriptContent.replace(/\.innerHTML = \\\\'([\\s\\S]*?)\\\\';/g, 
  function(match, p1) {
    // Keep the content as-is but fix the quoting
    return ".innerHTML = '" + p1 + "';";
  });

// Fix ternary with \\\\'  (e.g., transaction.type === \\\'income\\\' ? \\\'text-secondary\\\' : \\\'text-danger\\\')
scriptContent = scriptContent.replace(/=== \\\\'([^']*?)\\\\'/g, "=== '$1'");
scriptContent = scriptContent.replace(/!== \\\\'([^']*?)\\\\'/g, "!== '$1'");
scriptContent = scriptContent.replace(/\? \\\\'([^']*?)\\\\' :/g, "? '$1' :");
scriptContent = scriptContent.replace(/: \\\\'([^']*?)\\\\'/g, ": '$1'");
scriptContent = scriptContent.replace(/\\\+'([^']*?)\\\\'/g, "+ '$1'");

// Fix getAccountName object literals: \\\\'cash\\\\': \\\\'现金\\\\',
scriptContent = scriptContent.replace(/\\\\\\'([^']+?)\\\\'\\s*:/g, "'$1':");
scriptContent = scriptContent.replace(/:\\s*\\\\\\'([^']+?)\\\\'/g, ": '$1'");

// Fix \\'; at end of lines -> ';
scriptContent = scriptContent.replace(/\\';/g, "';");

// Fix standalone \\' -> ' (escaped single quotes in string contexts)
// Be careful not to break legitimate escapes
scriptContent = scriptContent.replace(/(?<!\\)\\\\'/g, "'");

// Now check if it compiles
try {
  new vm.Script(scriptContent);
  console.log('SUCCESS: Script compiles without errors!');
} catch(e) {
  console.log('STILL HAS ERROR:', e.message);
  const m = e.stack.match(/<anonymous>:(\d+):(\d+)/);
  if (m) {
    const scriptLine = parseInt(m[1]);
    const scriptLines = scriptContent.split('\n');
    const start = Math.max(0, scriptLine - 4);
    const end = Math.min(scriptLines.length, scriptLine + 4);
    console.log('\nContext around error (script line ' + scriptLine + '):');
    for (let j = start; j < end; j++) {
      const marker = (j === scriptLine - 1) ? ' >>> ' : '     ';
      console.log(marker + (j+1) + ': ' + scriptLines[j].substring(0, 200));
    }
  }
}

// Reconstruct the file
const newContent = content.substring(0, startIdx + '<script>'.length) + scriptContent + '\n' + content.substring(endIdx);
fs.writeFileSync('d:/XM/android-app-JZGJ/app/src/main/assets/index.html', newContent, 'utf8');
console.log('File saved.');
