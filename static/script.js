var MQ = MathQuill.getInterface(2);

var mathFieldSpan = document.getElementById('math-field');

var mathField = MQ.MathField(mathFieldSpan, {
  handlers: {
    edit: function() {
      var latex = mathField.latex();
      document.getElementById("latex").value = latex;
    }
  }
});


function run(){

fetch("/process",{
method:"POST",
headers:{"Content-Type":"application/json"},
body:JSON.stringify({
latex:document.getElementById("latex").value
})
})

.then(r=>r.json())

.then(data=>{
document.getElementById("output").value = data.output
})

}


function copyLatex(){
navigator.clipboard.writeText(
document.getElementById("latex").value
)
}

function copyOutput(){
navigator.clipboard.writeText(
document.getElementById("output").value
)
}