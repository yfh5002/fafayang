var fs = require('fs');
var vm = require('vm');

var htmlFile = 'd:/XM/android-app-JZGJ/app/src/main/assets/index.html';
var html = fs.readFileSync(htmlFile, 'utf8');

// Extract all script blocks
var scriptRegex = /<script[^>]*>([\s\S]*?)<\/script>/gi;
var matches = [];
var m;
while ((m = scriptRegex.exec(html)) !== null) {
  matches.push({ full: m[0], content: m[1], index: m.index });
}

// We focus on script #5 (the main one with errors)
var targetScript = matches[4]; // 0-indexed, so 5th script
var scriptContent = targetScript.content;
var lines = scriptContent.split('\n');

console.log('Total script lines: ' + lines.length);
console.log('Total script chars: ' + scriptContent.length);

// Find ALL multi-line string patterns:
// Pattern: a line ending with ' (opening quote) followed by non-JS lines, then closing '; 
// Also lines ending with \' (escaped quote opening)

function findMultiLineStrings(lines) {
  var results = [];
  for (var i = 0; i < lines.length; i++) {
    var trimmed = lines[i].trimEnd();
    // Check if line ends with ' or \' (potential string start that spans multiple lines)
    // A single-quoted string should end with '; or ', + ... on same line
    // If it ends with just ' or \' and next line looks like HTML/JSX, it's multi-line
    
    var endsWithQuote = /'\s*$/.test(trimmed);
    var endsWithEscapedQuote = /\\'\s*$/.test(trimmed);
    var endsWithDoubleEscQuote = /\\\\'\s*$/.test(trimmed);
    var endsWithTripleEscQuote = /\\\\\\'\s*$/.test(trimmed);
    
    if (endsWithQuote && !endsWithEscapedQuote) {
      // Ends with plain ' - check if it looks like assignment to innerHTML
      if (/=\s*['"]/.test(trimmed) || /\+\s*['"]\s*$/.test(trimmed) || /^\s*['"]/.test(trimmed)) {
        // Check if this looks like a string continuation (next line is not closing it)
        if (i + 1 < lines.length) {
          var nextTrimmed = lines[i + 1].trim();
          // If next line starts with HTML tag or has content that's not just a closing quote
          if (nextTrimmed && !nextTrimmed.match(/^['"]\s*[;,)\]]?\s*$/) && !nextTrimmed.match(/^[+\-]/)) {
            // Also check it's not a simple single-line string that just has trailing content
            var quoteCount = (trimmed.match(/'/g) || []).length;
            if (quoteCount % 2 !== 0) {
              // Odd number of quotes - likely an unclosed string
              results.push({ line: i + 1, text: trimmed.substring(0, 100), type: 'plain-quote' });
            }
          }
        }
      }
    }
    
    if (endsWithEscapedQuote && !endsWithDoubleEscQuote) {
      // Ends with \' (single backslash + quote)
      if (/=\s*/.test(trimmed) || /\+\s*$/.test(trimmed)) {
        results.push({ line: i + 1, text: trimmed.substring(0, 100), type: 'escaped-quote' });
      }
    }
    
    if (endsWithDoubleEscQuote && !endsWithTripleEscQuote) {
      // Ends with \\' (double backslash + quote)  
      if (/=\s*/.test(trimmed) || /\+\s*$/.test(trimmed)) {
        results.push({ line: i + 1, text: trimmed.substring(0, 100), type: 'double-escaped-quote' });
      }
    }
  }
  return results;
}

var multiLineStrings = findMultiLineStrings(lines);
console.log('\n--- Potential multi-line strings ---');
multiLineStrings.forEach(function(item) {
  console.log('  Line ' + item.line + ' [' + item.type + ']: ' + JSON.stringify(item.text));
});

// Now let's also find the quote patterns in detail
console.log('\n--- Detailed quote analysis (first 50 lines with backslash-quote) ---');
var count = 0;
for (var i = 0; i < lines.length && count < 50; i++) {
  if (lines[i].indexOf('\\') !== -1 && lines[i].indexOf("'") !== -1) {
    console.log('  Line ' + (i + 1) + ': ' + JSON.stringify(lines[i].substring(0, 150)));
    count++;
  }
}
