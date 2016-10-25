// customize-manage-rental-return-step-3.js

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
        $('#punch-section')
            .form({
                onSuccess: submitForm
            })
        ;
    })
;