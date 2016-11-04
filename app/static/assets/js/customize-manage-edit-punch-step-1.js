// customize-manage-edit-punch-step-1.js

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
        $('#punch-lesson')
            .form({
                onSuccess: submitForm
            })
        ;
    })
;