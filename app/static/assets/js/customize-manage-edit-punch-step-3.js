// customize-manage-edit-punch-step-3.js

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
        $('#confirm-punch')
            .form({
                onSuccess: submitForm
            })
        ;
    })
;