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