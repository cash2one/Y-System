// customize-manage-delete-announcement.js

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
        $('#delete-announcement')
            .form({
                onSuccess: submitForm
            })
        ;
    })
;