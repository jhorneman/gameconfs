// $.widget( "custom.catcomplete", $.ui.autocomplete, {
//    _renderMenu: function( ul, items ) {
//      var that = this,
//        currentCategory = "";
//      $.each( items, function( index, item ) {
//        if ( item.category != currentCategory ) {
//          ul.append( "<li class='ui-autocomplete-category'>" + item.category + "</li>" );
//          currentCategory = item.category;
//        }
//        that._renderItemData( ul, item );
//      });
//    }
//  });
//
//$(function() {
//var data = [
//  { label: "London", category: "Cities" },
//  { label: "San Francisco", category: "Cities" },
//  { label: "Amsterdam", category: "Cities" },
//  { label: "France", category: "Countries" },
//  { label: "California", category: "States" },
//  { label: "Europe", category: "Continents" }
//];
//
//$( "#search" ).catcomplete({
//  delay: 0,
//  source: data
//});
//});

$(function() {
    $('#location').tooltip()
        .click(function(){
            $('#search-form').show();
            $('#location').tooltip('destroy');
        });
    $('#cancel').tooltip()
        .click(function(){
            $('#search-form').hide();
            $('#location').tooltip();
        });
});
