var fs = require('fs');
var html = fs.readFileSync('d:/XM/android-app-JZGJ/app/src/main/assets/index.html', 'utf8');
var lines = html.split('\n');

var line = lines[4392];
// Find the section around 月
var idx = line.indexOf('\u6708');
if (idx === -1) idx = line.indexOf('\u66DC');
console.log("Around index " + idx + ":");
for (var j = Math.max(0, idx - 5); j <= Math.min(line.length - 1, idx + 10); j++) {
  console.log("  [" + j + "] 0x" + line.charCodeAt(j).toString(16) + " " + JSON.stringify(line[j]));
}
