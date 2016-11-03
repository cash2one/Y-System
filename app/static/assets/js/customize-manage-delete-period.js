// customize-manage-delete-period.js

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
        $('#delete-period')
            .form({
                onSuccess: submitForm
            })
        ;
    })
;