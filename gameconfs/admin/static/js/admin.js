$(document).ready(function() {
    var bodyId = $(document.body).attr('id');
    switch (bodyId) {
        case 'events_update':
        {
            initEventsUpdatePage();
        }
    }
});

function initEventsUpdatePage() {
    $('table tr td.event-url a')
    .on('click', function(evt) {
        var rowEl = $(evt.target).parent().parent(),
            eventId = rowEl.data('event-id'),
            ajax_url = '/admin/event/' + eventId.toString() + '/set_last_checked';

        $.post(ajax_url)
        .done(function(data, textStatus, jqXHR) {
            $('td.last-checked', rowEl).html('Checked');
        })
        .fail(function(jqXHR, textStatus, errorThrown) {
            console.error("Call to " + ajax_url + " failed. Status: " + textStatus + ", error: '" + errorThrown + "'.");
        });
    });

    $('table tr input[type=checkbox]')
    .on('click', function(evt) {
        var rowEl = $(evt.target).parent().parent(),
            eventId = rowEl.data('event-id'),
            ajax_url = '/admin/event/' + eventId.toString() + '/toggle_checking';

        $.post(ajax_url)
        .done(function(data, textStatus, jqXHR) {
            if (data.newState) {
                rowEl.removeClass('not-being-checked');
            } else {
                rowEl.addClass('not-being-checked');
            }
        })
        .fail(function(jqXHR, textStatus, errorThrown) {
            console.error("Call to " + ajax_url + " failed. Status: " + textStatus + ", error: '" + errorThrown + "'.");
        });
    });
}
