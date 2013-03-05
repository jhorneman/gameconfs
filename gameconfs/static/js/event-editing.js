$(document).ready(function() {
    var startDatePickerData,
        endDatePickerData;

    startDatePickerData = $('#start_date')
        .datepicker({
            'format': 'dd/mm/yyyy',
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

    endDatePickerData = $('#end_date')
        .datepicker({
            'format': 'dd/mm/yyyy',
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
});