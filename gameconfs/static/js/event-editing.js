$(document).ready(function() {
    var bodyId = $(document.body).attr('id');
    if (bodyId == "edit-event") {
        initEditEventPage();
    } else if (bodyId == "view-event") {
        initViewEventPage();
    }
});

function isEventValid() {
    var yearInStartDate, yearInEndDate, eventName, result, yearInTitle;

    yearInStartDate = parseInt($("#start_date").val().slice(0, 4));
    yearInEndDate = parseInt($("#end_date").val().slice(0, 4));

    if (yearInStartDate != yearInEndDate) {
        if (1 != confirm("This event starts in " + yearInStartDate.toString() + ", but it ends in "
         + yearInEndDate.toString() + ". Are you sure you want to submit this event?")) {
            return false;
        }
    }

    eventName = $("#name").val();
    result = new RegExp(".*(2\\d\\d\\d).*").exec(eventName);
    if (result) {
        yearInTitle = parseInt(result[1]);
        if (yearInStartDate != yearInTitle) {
            return (1 == confirm("The year in the event title is " + yearInTitle.toString() + ", while the one in the start date is "
             + yearInStartDate.toString() + ". Are you sure you want to submit this event?"));
        }
    }

    return true;
}

function initEditEventPage() {
    setUpDatePickers();

    // Set up typeahead
    $('#address').typeahead({
        name: 'cities',
        prefetch: '/data/cities.json',
        template: function(datum) {
            return '<p>'+datum.value+', '+datum.country+'</p>';
        },
        limit: 10
    });

    $('#series').typeahead({
        name: 'series',
        prefetch: '/data/series.json',
        limit: 10
    });

    $('#submit-button')
        .on('click', function(evt) {
            if (!isEventValid()) {
                evt.preventDefault();
            }
        });
}

// Doing this by hand instead of loading Modernizr just for this one function.
function supportsDateInputType() {
    var testInputElement, supportsFlag;

    testInputElement = document.createElement("input");
    testInputElement.setAttribute("type", "date");
    return testInputElement.type !== "text";
}

function setUpDatePickers() {
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
            if (1 != confirm("Are you sure you want to delete this event?")) {
                evt.preventDefault();
            }
        });
}
