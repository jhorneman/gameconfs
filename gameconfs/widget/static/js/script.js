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
            var container,
                css_link,
                userId,
                place,
                nrMonths,
                widgetWidth,
                widgetHeight,
                jsonpURL;

            container = $('#gameconfs-widget-container');
            container.addClass('cleanslate');

            /* Append CSS to head */
            css_link = $("<link>", {
                rel: "stylesheet",
                type: "text/css",
                href: "http://www.gameconfs.com/widget/v1/widget.css"
            });
            css_link.appendTo('head');

            /* Load widget parameters */
            userId = container.data('user-id');
            place = container.data('place');
            nrMonths = container.data('nr-months') || 3;
            widgetWidth = container.data('width') || 240;
            widgetHeight = container.data('height') || 400;

            /* Load and inject HTML */
            jsonpURL = "http://www.gameconfs.com/widget/v1/data.json?nr-months=" + encodeURIComponent(nrMonths);
            if (userId) {
                jsonpURL += "&user-id=" + encodeURIComponent(userId);
            }
            if (place) {
                jsonpURL += "&place=" + encodeURIComponent(place);
            }
            jsonpURL += "&callback=?";
            $.getJSON(jsonpURL, function(data) {
                container.html(data.html);
                container.attr('style', 'width: ' + widgetWidth + 'px !important; height: ' + widgetHeight + 'px !important;')
            });
        });
    }

})(); // We call our anonymous function immediately