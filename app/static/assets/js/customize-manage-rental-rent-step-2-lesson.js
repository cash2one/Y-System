// customize-manage-rental-rent-step-2-lesson.js

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
        $('#select-lesson')
            .form({
                onSuccess: submitForm
            })
        ;
    })
;