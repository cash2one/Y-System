// customize-manage-rental-rent-step-3-lesson.js

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
        $('#select-ipad')
            .form({
                onSuccess: submitForm
            })
        ;
    })
;