var fs = require('fs');
var html = fs.readFileSync('d:/XM/android-app-JZGJ/app/src/main/assets/index.html', 'utf8');
var lines = html.split('\n');

var line = lines[4392]; // line 4393
console.log("Full line:");
console.log(line);
console.log("\nLast 20 chars:");
for (var j = line.length - 20; j < line.length; j++) {
  console.log("  [" + j + "] 0x" + line.charCodeAt(j).toString(16) + " " + JSON.stringify(line[j]));
}
