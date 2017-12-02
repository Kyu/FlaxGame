/**
 * Created by P.O on 7/29/2017.
 * Filename: game.js
 */


$(document).ready(function() {
    $("a#logout").click(function(event){
       $.post(
          "/logout",
          {},
          function(data) {
             window.location = '/'
          }
       );
       return false;
    });



});
