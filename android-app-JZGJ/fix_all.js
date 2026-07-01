var fs = require('fs');
var vm = require('vm');

var htmlFile = 'd:/XM/android-app-JZGJ/app/src/main/assets/index.html';
var html = fs.readFileSync(htmlFile, 'utf8');

// Extract all script blocks
var scriptRegex = /<script[^>]*>([\s\S]*?)<\/script>/gi;
var matches = [];
var m;
while ((m = scriptRegex.exec(html)) !== null) {
  matches.push({ full: m[0], content: m[1], index: m.index, endIndex: m.index + m[0].length });
}

var targetIdx = 4; // 5th script (0-indexed)
var target = matches[targetIdx];
var scriptContent = target.content;
var scriptLines = scriptContent.split('\n');

console.log('Processing script #' + (targetIdx + 1) + ' (' + scriptLines.length + ' lines)...');

// Step 1: Find and fix multi-line innerHTML strings
// Pattern: line like "xxx.innerHTML = '" or "xxx.innerHTML += '" or "html += '"
// followed by HTML content lines, then a closing line with "';" or "\';"

function fixMultiLineStrings(lines) {
  var fixed = lines.slice();
  var fixes = [];
  var i = 0;
  
  while (i < fixed.length) {
    var line = fixed[i];
    var trimmed = line.trimEnd();
    
    // Detect potential multi-line string start
    // Patterns: xxx.innerHTML = ' or xxx.innerHTML = \' or html += ' etc.
    var startMatch = trimmed.match(/(\S+(?:innerHTML|outerHTML|textContent|html)\s*(\+?=)\s*)(')((?:\\')?)$/);
    
    if (!startMatch) {
      // Also try pattern: someString += '
      startMatch = trimmed.match(/(\S+\s*\+=\s*)(')((?:\\')?)$/);
    }
    
    if (startMatch) {
      var prefix = startMatch[1]; // e.g., "transactionElement.innerHTML = "
      var op = startMatch[2] || '+';
      var quote = startMatch[3]; // opening quote
      var escaped = startMatch[4]; // optional \' at end
      
      // Collect continuation lines until we find the closing
      var contentLines = [];
      var j = i + 1;
      var found = false;
      
      while (j < fixed.length && j < i + 100) {
        var nextLine = fixed[j];
        var nextTrimmed = nextLine.trim();
        
        // Check if this is the closing line
        // Patterns: '; or \'; or \\'; or just '; at start
        if (nextTrimmed.match(/^\\*'?';\s*$/) || nextTrimmed === "';") {
          found = true;
          break;
        }
        
        // If line looks like code (not HTML content), stop
        // HTML content lines typically start with < or whitespace+< or have class= etc.
        if (nextTrimmed.match(/^(var |let |const |function |if |for |while |return |\/\/)/)) {
          break;
        }
        
        contentLines.push(nextLine);
        j++;
      }
      
      if (found && contentLines.length > 0) {
        // We have a multi-line string. Merge it into a single line using string concatenation.
        // The content is HTML that was meant to be a template string
        
        // Clean up the content lines - they are HTML content for innerHTML
        var contentStr = contentLines.map(function(cl) {
          // Each content line is raw HTML that should be part of the string
          // We need to handle any quotes within the HTML content
          return cl.trim();
        }).join('');
        
        // Now we need to properly quote this content
        // The content may contain single quotes, so we use backtick (template literal)
        // Or we can escape single quotes
        
        // Check if the content has backticks
        if (contentStr.indexOf('`') !== -1) {
          // Use backtick but escape any existing backticks
          contentStr = contentStr.replace(/`/g, '\\`');
        }
        
        var newLine = prefix + '`' + contentStr + '`;';
        
        // Also handle the escaped opening - if it was \' we need to handle that
        if (escaped) {
          // The line ended with \' which means it was already starting a string
          // We need to adjust
          // Actually, if escaped is \', the line in JS is: xxx = '...\' 
          // which means the string hasn't been closed yet
          // Just use the merged version
        }
        
        fixed[i] = newLine;
        // Remove the content lines and closing line
        for (var k = i + 1; k <= j; k++) {
          fixed[k] = null; // mark for removal
        }
        
        fixes.push({ line: i + 1, original: trimmed.substring(0, 80), newLine: newLine.substring(0, 80) + '...' });
        
        i = j + 1;
      } else {
        i++;
      }
    } else {
      i++;
    }
  }
  
  // Remove null lines
  fixed = fixed.filter(function(l) { return l !== null; });
  
  return { lines: fixed, fixes: fixes };
}

var result = fixMultiLineStrings(scriptLines);
scriptLines = result.lines;

console.log('\nFixed ' + result.fixes.length + ' multi-line strings:');
result.fixes.forEach(function(f) {
  console.log('  Line ' + f.line + ': ' + JSON.stringify(f.original));
});

// Step 2: Fix escaped quotes in string assignments
// Pattern: 'value\\';  should be 'value';
// The \\' at the end of string adds an unwanted backslash
var escQuoteFixes = 0;
for (var i = 0; i < scriptLines.length; i++) {
  // Replace pattern: = 'something\\';  -> = 'something';
  // But NOT in HTML attribute contexts or string concatenation contexts
  scriptLines[i] = scriptLines[i].replace(/='([^']*)\\'/g, function(match, content) {
    escQuoteFixes++;
    return "='" + content + "'";
  });
  
  // Also handle: className = 'something\\';
  scriptLines[i] = scriptLines[i].replace(/= '([^']*)\\'/g, function(match, content) {
    escQuoteFixes++;
    return "= '" + content + "'";
  });
}

console.log('\nFixed ' + escQuoteFixes + ' escaped quotes in assignments');

// Step 3: Reassemble the HTML
var newScriptContent = scriptLines.join('\n');
var newHtml = html.substring(0, target.index) + '<script>' + newScriptContent + '</script>' + html.substring(target.endIndex);

// Step 4: Validate
console.log('\nValidating...');
var newMatches = [];
while ((m = scriptRegex.exec(newHtml)) !== null) {
  newMatches.push(m[1]);
}

var allOk = true;
for (var s = 0; s < newMatches.length; s++) {
  try {
    new vm.Script(newMatches[s]);
  } catch(e) {
    allOk = false;
    var errLines = newMatches[s].split('\n');
    console.log('ERROR in script #' + (s + 1) + ': ' + e.message);
    // Find the error location
    var errMatch = e.stack && e.stack.match(/<anonymous>:(\d+)/);
    if (errMatch) {
      var errLine = parseInt(errMatch[1]);
      console.log('  Near line ' + errLine + ':');
      for (var k = Math.max(0, errLine - 2); k <= Math.min(errLines.length - 1, errLine + 2); k++) {
        console.log('    ' + (k + 1) + ': ' + JSON.stringify(errLines[k].substring(0, 120)));
      }
    }
  }
}

if (allOk) {
  console.log('\nAll scripts are syntactically valid!');
  // Save the file
  fs.writeFileSync(htmlFile, newHtml, 'utf8');
  console.log('File saved to ' + htmlFile);
} else {
  console.log('\nStill have errors. Not saving.');
  // Save to temp file for inspection
  fs.writeFileSync('d:/XM/android-app-JZGJ/app/src/main/assets/index_fixed.html', newHtml, 'utf8');
  console.log('Saved to index_fixed.html for inspection');
}
