// customize-manage-edit-punch-step-1.js

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