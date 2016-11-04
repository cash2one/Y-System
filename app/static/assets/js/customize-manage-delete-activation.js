// customize-manage-delete-activation.js

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
        $('#delete-activation')
            .form({
                onSuccess: submitForm
            })
        ;
    })
;