// customize-manage-delete-activation.js

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
        $('#delete-activation')
            .form({
                onSuccess: submitForm
            })
        ;
    })
;