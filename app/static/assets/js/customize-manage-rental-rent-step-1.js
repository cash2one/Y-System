// customize-manage-rental-rent-step-1.js

$('select.dropdown')
  .dropdown()
;

$('table')
    .tablesort()
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
        $('#booking-code')
            .form({
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