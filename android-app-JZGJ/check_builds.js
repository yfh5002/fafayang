var fs = require('fs');
var vm = require('vm');

// Check if the build copies have valid syntax
['debug', 'release'].forEach(function(variant) {
  var path = 'd:/XM/android-app-JZGJ/app/build/intermediates/assets/' + variant + '/index.html';
  try {
    var content = fs.readFileSync(path, 'utf8');
    var startMarker = '<script>\n  // ====================';
    var startIdx = content.indexOf(startMarker);
    if (startIdx === -1) {
      console.log(variant + ': No main script found');
      return;
    }
    var endIdx = content.indexOf('</script>', startIdx + 100);
    var script = content.substring(startIdx + '<script>'.length, endIdx);
    
    try {
      new vm.Script(script);
      console.log(variant + ': SYNTAX OK (script length: ' + script.length + ')');
    } catch(e) {
      console.log(variant + ': SYNTAX ERROR - ' + e.message);
    }
  } catch(e) {
    console.log(variant + ': ' + e.message);
  }
});
