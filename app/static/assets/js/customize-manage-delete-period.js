// customize-manage-delete-period.js

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
        $('#delete-period')
            .form({
                onSuccess: submitForm
            })
        ;
    })
;