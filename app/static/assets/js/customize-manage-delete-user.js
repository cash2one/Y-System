// customize-manage-delete-user.js

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
        $('#delete-user')
            .form({
                onSuccess: submitForm
            })
        ;
    })
;