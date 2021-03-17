/* From Materialize (Mobile collapse Button) https://materializecss.com/navbar.html 
and from Code Institute Backend Development Mini Project */

$(document).ready(function(){
    $('.sidenav').sidenav({edge: "right"});
    $('.parallax').parallax();
    $('.tabs').tabs();
    $('.collapsible').collapsible();
    $('.tooltipped').tooltip();
    $('select').formSelect();
    $('.chips-placeholder').chips({
        placeholder: 'Enter a tag',
        secondaryPlaceholder: '+Tag',
    });
  });

  

