var fs = require('fs');
var html = fs.readFileSync('d:/XM/android-app-JZGJ/app/src/main/assets/index.html', 'utf8');
var lines = html.split('\n');

// Find all lines with \'; at end (which is \ + ' + ;)
// In the file, \\';  means bytes: \, ', ;
// This is INVALID JS because \' is an escaped quote inside a string that never closes
var problemLines = [];
for (var i = 0; i < lines.length; i++) {
  // Pattern: the line ends with \';  (a backslash followed by quote followed by semicolon)
  // But we need to distinguish from valid patterns like: 'some\\';  (string with escaped backslash)
  // The problem pattern is when \' appears at the start of what should be a closing string
  
  // Check for pattern: + '\\'; or = '\\';
  // In file bytes: + '\';  (where \ is literal backslash)
  if (/[+\-=]\s*'\\';\s*$/.test(lines[i])) {
    problemLines.push({ line: i + 1, text: lines[i].trim() });
  }
}

console.log("Lines with problematic escape pattern:");
problemLines.forEach(function(p) {
  console.log('  HTML line ' + p.line + ': ' + p.text.substring(0, 120));
});
console.log('Total: ' + problemLines.length);
