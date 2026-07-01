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

var targetIdx = 4;
var target = matches[targetIdx];
var scriptContent = target.content;
var scriptLines = scriptContent.split('\n');

console.log('Processing script #' + (targetIdx + 1) + ' (' + scriptLines.length + ' lines)...');

// Step 1: Fix multi-line innerHTML strings
function fixMultiLineStrings(lines) {
  var fixed = lines.slice();
  var fixes = [];
  var i = 0;
  
  while (i < fixed.length) {
    var line = fixed[i];
    var trimmed = line.trimEnd();
    
    // Detect: xxx.innerHTML = ' or xxx.innerHTML = \' or html += ' etc.
    // The key is: line ends with ' and next line starts with HTML content (not JS)
    var isAssignment = /\binnerHTML\s*(\+?=)\s*$/.test(trimmed) || 
                       /\bouterHTML\s*(\+?=)\s*$/.test(trimmed) ||
                       /\bhtml\s*\+=\s*$/.test(trimmed);
    
    if (!isAssignment) {
      // Also check patterns like: xxx = '
      isAssignment = /['"]?\s*$/.test(trimmed) && 
                     (/\w+\s*(\+?=)\s*['"]?\s*$/.test(trimmed) && trimmed.endsWith("'"));
    }
    
    // Simpler approach: look for lines ending with = ' or = \' or += ' or += \'
    var assignMatch = trimmed.match(/^(\s*\S+(?:\s*[\w.]*\s*(\+?=)?)\s*)(\\?'|\\?'|')(\s*)$/);
    if (!assignMatch) {
      assignMatch = trimmed.match(/^(\s*(?:[\w.]+)\s*(?:innerHTML|outerHTML|html|textContent)\s*\+?=\s*)(\\?')(\s*)$/);
    }
    
    if (!assignMatch) {
      // Try a broader pattern for lines ending with a single/double quote
      // that look like string assignments
      if (/=\s*'?$/i.test(trimmed) || /\+=\s*'?$/i.test(trimmed)) {
        // Check if next line is HTML content
        if (i + 1 < fixed.length) {
          var nextTrimmed = fixed[i + 1].trim();
          if (nextTrimmed && (nextTrimmed.startsWith('<') || /^\s+\</.test(fixed[i + 1]))) {
            assignMatch = [trimmed, trimmed.match(/.*=\s*/)[0], '=', "'"];
          }
        }
      }
    }
    
    if (assignMatch && assignMatch[2] !== undefined) {
      var prefix = assignMatch[1];
      var j = i + 1;
      var contentLines = [];
      var found = false;
      
      while (j < fixed.length && j < i + 100) {
        var nextLine = fixed[j];
        var nextTrimmed = nextLine.trim();
        
        // Check for closing patterns
        if (/^\\*'?';\s*$/.test(nextTrimmed) || nextTrimmed === "';") {
          found = true;
          break;
        }
        
        // Stop if it looks like JS code
        if (/^(var |let |const |function |if\s*\(|for\s*\(|while\s*\(|return |\/\/\s)/.test(nextTrimmed)) {
          break;
        }
        
        contentLines.push(nextLine);
        j++;
      }
      
      if (found && contentLines.length > 0) {
        var contentStr = contentLines.map(function(cl) { return cl.trim(); }).join('');
        var newLine = prefix + '`' + contentStr + '`;';
        
        fixed[i] = newLine;
        for (var k = i + 1; k <= j; k++) {
          fixed[k] = null;
        }
        
        fixes.push({ line: i + 1, original: trimmed.substring(0, 80) });
        i = j + 1;
        continue;
      }
    }
    
    i++;
  }
  
  fixed = fixed.filter(function(l) { return l !== null; });
  return { lines: fixed, fixes: fixes };
}

var result = fixMultiLineStrings(scriptLines);
scriptLines = result.lines;

console.log('Fixed ' + result.fixes.length + ' multi-line strings');

// Step 2: Fix ONLY escaped quotes at the END of simple string assignments
// Pattern: 'value\\';  -> 'value';  (assignment where string ends with \\')
// But DO NOT touch \\' inside onclick attributes or string concatenation
var escFixes = 0;
for (var i = 0; i < scriptLines.length; i++) {
  var line = scriptLines[i];
  
  // Only fix patterns like: var x = 'something\\';  or  .className = 'something\\';
  // These are simple string assignments where \\' before ; is wrong
  // Pattern: = 'content\\';  where content has no quotes inside
  if (/=\s*'[^']*\\'\s*;/.test(line)) {
    scriptLines[i] = line.replace(/= '([^']*?)\\'/, "= '$1'");
    escFixes++;
  }
}

console.log('Fixed ' + escFixes + ' escaped quotes in simple assignments');

// Step 3: Fix known syntax bugs (extra parenthesis, missing semicolons, etc.)
var bugFixes = 0;
for (var i = 0; i < scriptLines.length; i++) {
  // Fix: return new Date(b.date) - new Date(a.date)); -> remove extra )
  // a.date)); should be a.date);
  if (/Date\(a\.date\)\)\s*;/.test(scriptLines[i])) {
    scriptLines[i] = scriptLines[i].replace(/Date\(a\.date\)\)\s*;/, 'Date(a.date);');
    bugFixes++;
  }
}
console.log('Fixed ' + bugFixes + ' syntax bugs');

// Step 4: Reassemble and validate
var newScriptContent = scriptLines.join('\n');
var newHtml = html.substring(0, target.index) + '<script>' + newScriptContent + '</script>' + html.substring(target.endIndex);

// Validate all scripts
scriptRegex.lastIndex = 0;
matches = [];
while ((m = scriptRegex.exec(newHtml)) !== null) matches.push(m[1]);

var allOk = true;
var maxIterations = 10;
var iteration = 0;

while (!allOk && iteration < maxIterations) {
  iteration++;
  console.log('\n--- Validation iteration ' + iteration + ' ---');
  allOk = true;
  var scriptContent2 = scriptLines.join('\n');
  
  try {
    new vm.Script(scriptContent2);
  } catch(e) {
    allOk = false;
    var errLines = scriptLines;
    console.log('ERROR: ' + e.message);
    var errMatch = e.stack && e.stack.match(/<anonymous>:(\d+)/);
    if (errMatch) {
      var errLine = parseInt(errMatch[1]);
      console.log('  Near line ' + errLine + ':');
      for (var k = Math.max(0, errLine - 3); k <= Math.min(errLines.length - 1, errLine + 3); k++) {
        var marker = (k === errLine - 1) ? '>>>' : '   ';
        console.log('  ' + marker + ' ' + (k + 1) + ': ' + errLines[k].substring(0, 150));
      }
      
      // Try to auto-fix common issues
      var problemLine = errLines[errLine - 1] || '';
      
      // Fix extra closing paren: a.date)); -> a.date);
      if (/Date\(a\.date\)\)\s*;/.test(problemLine)) {
        scriptLines[errLine - 1] = problemLine.replace(/Date\(a\.date\)\)\s*;/, 'Date(a.date);');
        console.log('  AUTO-FIX: Removed extra ) on line ' + errLine);
        continue;
      }
      
      // Fix extra closing paren: b.date)); -> b.date);
      if (/Date\(b\.date\)\)\s*;/.test(problemLine)) {
        scriptLines[errLine - 1] = problemLine.replace(/Date\(b\.date\)\)\s*;/, 'Date(b.date);');
        console.log('  AUTO-FIX: Removed extra ) on line ' + errLine);
        continue;
      }
      
      // Fix onclick with unescaped quotes: func('' + var + '')  -> func(\'' + var + '\')
      // This pattern: onclick="func('' + var + '')"
      // Should be: onclick="func(\'" + var + "\')"
      if (/onclick=.*''\s*\+\s*\w+/.test(problemLine)) {
        scriptLines[errLine - 1] = problemLine.replace(/''(\s*\+\s*\w+\s*\+\s*)''/g, "'\\'$1\\''");
        console.log('  AUTO-FIX: Fixed onclick quotes on line ' + errLine);
        continue;
      }
      
      console.log('  No auto-fix available. Manual fix needed.');
    }
  }
}

if (allOk) {
  console.log('\n=== All scripts are syntactically valid! ===');
  var newScriptContent = scriptLines.join('\n');
  var newHtml = html.substring(0, target.index) + '<script>' + newScriptContent + '</script>' + html.substring(target.endIndex);
  fs.writeFileSync(htmlFile, newHtml, 'utf8');
  console.log('File saved successfully.');
} else {
  console.log('\nCould not auto-fix all errors. Saving to temp file for inspection.');
  var newScriptContent = scriptLines.join('\n');
  var newHtml = html.substring(0, target.index) + '<script>' + newScriptContent + '</script>' + html.substring(target.endIndex);
  fs.writeFileSync('d:/XM/android-app-JZGJ/app/src/main/assets/index_fixed2.html', newHtml, 'utf8');
}
