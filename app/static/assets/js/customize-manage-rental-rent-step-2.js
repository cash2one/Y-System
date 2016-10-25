// customize-manage-rental-rent-step-2.js

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
        $('#select-ipad')
            .form({
                onSuccess: submitForm
            })
        ;
    })
;