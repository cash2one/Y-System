// customize-manage-delete-ipad.js

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
        $('#delete-ipad')
            .form({
                onSuccess: submitForm
            })
        ;
    })
;