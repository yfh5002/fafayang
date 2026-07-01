var fs = require('fs');
var vm = require('vm');
var cheerio;

try { cheerio = require('cheerio'); } catch(e) { cheerio = null; }

var html = fs.readFileSync('d:/XM/android-app-JZGJ/app/src/main/assets/index.html', 'utf8');

// Extract all script blocks
var scriptRegex = /<script[^>]*>([\s\S]*?)<\/script>/gi;
var match;
var scriptNum = 0;
var allOk = true;

while ((match = scriptRegex.exec(html)) !== null) {
  scriptNum++;
  var scriptContent = match[1].trim();
  if (!scriptContent) continue;
  
  try {
    new vm.Script(scriptContent);
    console.log('Script #' + scriptNum + ': OK (' + scriptContent.split('\n').length + ' lines, ' + scriptContent.length + ' chars)');
  } catch(e) {
    allOk = false;
    var lines = scriptContent.split('\n');
    console.log('Script #' + scriptNum + ': ERROR - ' + e.message);
    console.log('  Lines: ' + lines.length + ', Chars: ' + scriptContent.length);
    
    // Find the line number in the script
    var lineMatch = e.stack && e.stack.match(/<anonymous>:(\d+)/);
    if (lineMatch) {
      var errLine = parseInt(lineMatch[1]);
      console.log('  Error near script line ' + errLine);
      for (var i = Math.max(0, errLine-3); i <= Math.min(lines.length-1, errLine+3); i++) {
        var marker = (i === errLine-1) ? '>>>' : '   ';
        var linePreview = lines[i].substring(0, 120);
        console.log('  ' + marker + ' ' + (i+1) + ': ' + JSON.stringify(linePreview));
      }
    }
  }
}

if (allOk) {
  console.log('\nAll scripts are syntactically valid!');
} else {
  console.log('\nThere are syntax errors to fix.');
}

// Also count problematic patterns
console.log('\n--- Pattern analysis ---');
var mainScript = html.match(/<script[^>]*>([\s\S]*?)<\/script>/gi);
if (mainScript) {
  // Focus on the last (main) script
  var lastScript = mainScript[mainScript.length - 1];
  var content = lastScript.replace(/<\/?script[^>]*>/gi, '');
  
  // Count patterns
  var patterns = [
    { name: "backslash-quote (\\')", regex: /\\'/g },
    { name: "double-backslash-quote (\\\\')", regex: /\\\\'/g },
    { name: "triple-backslash-quote (\\\\\\')", regex: /\\\\\\'/g },
    { name: "quad-backslash-quote (\\\\\\\\')", regex: /\\\\\\\\'/g },
  ];
  
  patterns.forEach(function(p) {
    var matches = content.match(p.regex);
    console.log(p.name + ': ' + (matches ? matches.length : 0) + ' occurrences');
  });
  
  // Find lines ending with odd patterns (potential multi-line strings)
  var lines = content.split('\n');
  var suspiciousLines = [];
  for (var i = 0; i < lines.length; i++) {
    var l = lines[i].trim();
    if (l.match(/=\s*.*['"]$/) && !l.match(/['"]\s*[;,]?\s*$/)) {
      // Line ends with a quote but no semicolon or comma after it
      if (!l.match(/['"][;,]\s*$/) && !l.match(/\/\/.*$/)) {
        suspiciousLines.push(i+1);
      }
    }
  }
  if (suspiciousLines.length > 0 && suspiciousLines.length <= 20) {
    console.log('\nSuspicious lines (may start multi-line strings):');
    suspiciousLines.forEach(function(ln) {
      console.log('  Script line ' + ln + ': ' + JSON.stringify(lines[ln-1].substring(0, 100)));
    });
  } else if (suspiciousLines.length > 20) {
    console.log('\nToo many suspicious lines to list: ' + suspiciousLines.length);
  }
}
