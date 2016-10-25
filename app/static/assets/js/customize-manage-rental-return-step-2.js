// customize-manage-rental-return-step-2.js

$('select.dropdown')
  .dropdown()
;

$('.message .close')
    .on('click', function() {
        $(this)
            .closest('.message')
            .transition('fade')
        ;
    })
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