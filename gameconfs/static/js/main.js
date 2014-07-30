;(function($, exports) {
    exports.submitFeedbackDialog = function() {
        $("#feedbackForm").modal("hide");

        $.ajax('/feedback', {
            data:           $("#feedbackText").val(),
            processData:    false,
            type:           "POST"
        })
        .done(function(data, textStatus, jqXHR) {
            alert("Thanks for your feedback!");
        })
        .fail(function(jqXHR, textStatus, errorThrown) {
            alert("Something went wrong when sending your feedback. Sorry!");
        });
    };
}(jQuery, window));

/**
* Function that tracks a click on an outbound link in Google Analytics.
* This function takes a valid URL string as an argument, and uses that URL string
* as the event label.
*/
var trackOutboundLink = function(url) {
   ga('send', 'event', 'outbound', 'click', url, {'hitCallback':
     function () {
     document.location = url;
     }
   });
}

var trackSponsorLink = function(url) {
   ga('send', 'event', 'sponsor', 'click', url, {'hitCallback':
     function () {
     document.location = url;
     }
   });
}
