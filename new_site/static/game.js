/**
 * Created by GP on 7/29/2017.
 * Filename: game.js
 */

function reload() {
    window.location = '/'
}

$(document).ready(function() {
    $("a#logout").click(function(event){
       $.post(
          "/logout",
          {},
          function(data) {
             reload()
          }
       );
       return false;
    });



});
