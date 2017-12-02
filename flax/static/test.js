/* Filename: custom.js */
function reload() {
    window.location = '/'
}
$(document).ready(function() {
    $("#logout").click(function(event){
       $.post(
          "/logout",
          {},
          function(data) {
             reload()
          }
       );
    });

});