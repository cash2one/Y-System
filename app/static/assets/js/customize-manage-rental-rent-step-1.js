// customize-manage-rental-rent-step-1.js

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
        $('#booking-code')
            .form({
                onSuccess: submitForm,
                fields: {
                    booking_code: {
                        identifier  : 'booking_code',
                        rules: [
                            {
                                type   : 'empty',
                                prompt : '请输入预约码'
                            }
                        ]
                    }
                }
            })
        ;
    })
;