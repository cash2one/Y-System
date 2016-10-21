// customize-manage-delete-ipad.js

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
        $('#delete-ipad')
            .form({
                onSuccess: submitForm
            })
        ;
    })
;