var fs = require('fs');
var html = fs.readFileSync('d:/XM/android-app-JZGJ/app/src/main/assets/index.html', 'utf8');
var lines = html.split('\n');

// Find all lines ending with \';  (single backslash before closing quote)
// This is: string contains content, then \'; at the end
// In JS this is INVALID because \' is an escape sequence that doesn't close the string
// Fix: remove the backslash

var count = 0;
for (var i = 0; i < lines.length; i++) {
  var line = lines[i];
  
  // Pattern: non-whitespace char followed by \';
  // This means the string has a stray backslash before the closing quote
  // e.g., 'text\';  should be 'text';
  // But we need to be careful not to break valid patterns like:
  // 'path\\';  which is a string ending with a backslash (valid: \\ = literal \)
  
  // Match: something\';  but NOT something\\';  (which is valid)
  // Regex: [^\\\s]\\';  at end of line
  if (/[^\\]\s*'\\';\s*$/.test(line) || /[^\\s]'\\';\s*$/.test(line)) {
    console.log("Line " + (i+1) + ": " + line.trim().substring(0, 100));
    count++;
  }
}
console.log("\nTotal problematic lines: " + count);
