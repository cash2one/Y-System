// customize-manage-rental-exchange-step-3.js

$('.message .close')
    .on('click', function() {
        $(this)
            .closest('.message')
            .transition('fade')
        ;
    })
;

$('select.dropdown')
    .dropdown()
;

$(document)
    .ready(function() {
        $('#punch-section')
            .form({
                onSuccess: submitForm
            })
        ;
    })
;