$(document).ready(function() {
    var bodyId = $(document.body).attr('id');
    if (bodyId == "edit-event") {
        initEditEventPage();
    } else if (bodyId == "view-event") {
        initViewEventPage();
    }
});

// Doing this by hand instead of loading Modernizr just for this one function.
function supportsDateInputType() {
    var testInputElement, supportsFlag;

    testInputElement = document.createElement("input");
    testInputElement.setAttribute("type", "date");
    return testInputElement.type !== "text";
}

function initEditEventPage() {
    var startDatePicker,
        endDatePicker,
        startDatePickerData,
        endDatePickerData;

    if (supportsDateInputType()) {
        return;
    }

    startDatePicker = $('#start_date');

    startDatePickerData = startDatePicker
        .datepicker({
            'format': 'yyyy-mm-dd',
            'weekStart': 1
        })
        .on('changeDate', function(evt) {
            if (evt.date.valueOf() > endDatePickerData.date.valueOf()) {
                endDatePickerData.setValue(new Date(evt.date));
            }
            endDatePickerData.fill();       // To re-evaluate disabled state of days
            startDatePickerData.hide();
            $('#end_date')[0].focus();
        })
        .data("datepicker");

    endDatePicker = $('#end_date');

    endDatePickerData = endDatePicker
        .datepicker({
            'format': 'yyyy-mm-dd',
            'weekStart': 1,
            'onRender': function(date) {
                return date.valueOf() < startDatePickerData.date.valueOf() ? 'disabled' : '';
            }
        })
        .on('changeDate', function(evt) {
            if (evt.date.valueOf() < startDatePickerData.date.valueOf()) {
                endDatePickerData.setValue(new Date(startDatePickerData.date));
            }
            endDatePickerData.hide();
        })
        .data("datepicker");
}

function initViewEventPage() {
    $('#delete-button')
        .on('click', function(evt) {
            if (!confirm("Are you sure you want to delete this event?")) {
                evt.preventDefault();
            }
        });
}
