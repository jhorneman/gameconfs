// (Taken from http://alexmarandon.com/articles/web_widget_jquery/)

(function() {
    // Localize jQuery variable
    var jQuery;

    /******** Load jQuery if not present *********/
    if (window.jQuery === undefined || window.jQuery.fn.jquery !== '1.7.2') {
        var script_tag = document.createElement('script');
        script_tag.setAttribute("type","text/javascript");
        script_tag.setAttribute("src",
            "http://ajax.googleapis.com/ajax/libs/jquery/1.7.2/jquery.min.js");
        if (script_tag.readyState) {
            script_tag.onreadystatechange = function () { // For old versions of IE
                if (this.readyState == 'complete' || this.readyState == 'loaded') {
                    scriptLoadHandler();
                }
            };
        } else { // Other browsers
            script_tag.onload = scriptLoadHandler;
        }
        // Try to find the head, otherwise default to the documentElement
        (document.getElementsByTagName("head")[0] || document.documentElement).appendChild(script_tag);
    } else {
        // The jQuery version on the window is the one we want to use
        jQuery = window.jQuery;
        main();
    }

    /******** Called once jQuery has loaded ******/
    function scriptLoadHandler() {
        // Restore $ and window.jQuery to their previous values and store the
        // new jQuery in our local jQuery variable
        jQuery = window.jQuery.noConflict(true);
        // Call our main function
        main();
    }

    /******** Our main function ********/
    function main() {
        jQuery(document).ready(function($) {
            $('#gameconfs-widget-container').addClass('cleanslate');

            /******* Load CSS *******/
            var css_link = $("<link>", {
                rel: "stylesheet",
                type: "text/css",
                href: "widget/v1/widget.css"
            });
            css_link.appendTo('head');

            /******* Load HTML *******/
            var userId = jQuery("#gameconfs-widget-container").data('user-id');
            var place = jQuery("#gameconfs-widget-container").data('place');
            var nrMonths = jQuery("#gameconfs-widget-container").data('nr-months');
            if (nrMonths === undefined) {
                nrMonths = 3;
            }
            console.log(nrMonths);
            var jsonp_url = "widget/v1/data.json?nr-months=" + encodeURIComponent(nrMonths);
            if (userId) {
                jsonp_url += "&user-id=" + encodeURIComponent(userId);
            }
            if (place) {
                jsonp_url += "&place=" + encodeURIComponent(place);
            }
            jsonp_url += "&callback=?";
            $.getJSON(jsonp_url, function(data) {
                $('#gameconfs-widget-container').html(data.html);
            });
        });
    }

})(); // We call our anonymous function immediately