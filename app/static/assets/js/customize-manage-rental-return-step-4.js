// customize-manage-rental-return-step-4.js

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
        $('#confirm-punch')
            .form({
                onSuccess: submitForm
            })
        ;
    })
;