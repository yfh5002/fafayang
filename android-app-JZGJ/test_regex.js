// The line from the file: transactionElement.innerHTML = \\'
// In the file, the bytes are: ... = \ \ ' (backslash, backslash, quote)
// In JS string literal: "transactionElement.innerHTML = \\\\'"
// In actual JS memory: transactionElement.innerHTML = \\' (backslash, backslash, quote)

// Test if regex /=\s*\\?'$/ matches this
var line = "transactionElement.innerHTML = \\'"; // This is what we'd read from file
// Actually, when we read the file, the content is: ... = \\'
// In the JS string: "transactionElement.innerHTML = \\\\'"
console.log("Line:", line);
console.log("Match:", /=\s*\\?'$/.test(line));

// Also test with just a ' at the end  
var line2 = "innerHTML = '";
console.log("Line2:", line2);
console.log("Match2:", /=\s*\\?'$/.test(line2));

// Test with \' at the end
// In the actual file bytes: \ \' (backslash, quote)
// When read with fs.readFileSync, we get the literal chars \ and '
// In JS, that's the string "innerHTML = \\'"
var line3 = "innerHTML = \\'";
console.log("Line3:", line3);
console.log("Match3:", /=\s*\\?'$/.test(line3));
console.log("Line3 length:", line3.length, "last char:", line3.charCodeAt(line3.length-1));
