// a simple TeX-input example

var mathjax = require("mathjax-node");

mathjax.config({
  MathJax: {
    // traditional MathJax configuration
  }
});

mathjax.start();

process.stdin.pipe(require('split')()).on('data', function processLine(line) {
  mathjax.typeset({
    math: line,
    format: "inline-TeX",
    svg: true
  }, function (data) {
    if (!data.errors)
      console.log(data.svg);
    process.exit()
  });
});

