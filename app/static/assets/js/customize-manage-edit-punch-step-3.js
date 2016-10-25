// customize-manage-edit-punch-step-3.js

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