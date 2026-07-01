var fs = require('fs');
var path = 'd:/XM/android-app-JZGJ/app/build/intermediates/assets/debug/index.html';
var content = fs.readFileSync(path, 'utf8');
var lines = content.split('\n');
for (var i = 908; i < 935; i++) {
  console.log((i+1) + ': ' + lines[i]);
}
