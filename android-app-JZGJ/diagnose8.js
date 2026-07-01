var fs = require('fs');
var vm = require('vm');
var html = fs.readFileSync('d:/XM/android-app-JZGJ/app/src/main/assets/index.html', 'utf8');
var scriptRegex = /<script[^>]*>([\s\S]*?)<\/script>/gi;
var matches = [];
var m;
while ((m = scriptRegex.exec(html)) !== null) matches.push(m[1]);

var scriptContent = matches[4];
var lines = scriptContent.split('\n');

// Find ALL lines that start/end with a lone quote and are followed by HTML content
// This includes: return ', xxx.innerHTML = ', html += ', etc.
var multiLineStarts = [];
for (var i = 0; i < lines.length; i++) {
  var trimmed = lines[i].trimEnd();
  
  // Check if line ends with an unmatched quote that's part of a string expression
  // Count quotes on the line - if odd number, there's an unclosed string
  var singleQuotes = (trimmed.match(/'/g) || []).length;
  
  // But we need to exclude escaped quotes: \' counts as part of the string, not a delimiter
  var cleanTrimmed = trimmed.replace(/\\'/g, ''); // remove escaped quotes for counting
  var cleanSingleQuotes = (cleanTrimmed.match(/'/g) || []).length;
  
  if (cleanSingleQuotes % 2 !== 0 && cleanSingleQuotes > 0) {
    // Odd number of unescaped single quotes - likely an unclosed string
    // Check if next line starts with HTML content or whitespace+HTML
    if (i + 1 < lines.length) {
      var nextTrimmed = lines[i + 1].trim();
      // HTML content: starts with < or has class=, style=, etc.
      if (nextTrimmed.startsWith('<') || /^\s+</.test(lines[i + 1]) || 
          /^[a-z]+-/.test(nextTrimmed)) {
        multiLineStarts.push({ line: i + 1, text: trimmed.substring(0, 100) });
      }
    }
  }
}

console.log("Multi-line string starts found: " + multiLineStarts.length);
multiLineStarts.forEach(function(item) {
  console.log("  Script line " + item.line + ": " + JSON.stringify(item.text));
});
