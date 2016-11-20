// customize-manage-rental-exchange-step-1.js

$('.message .close')
    .on('click', function() {
        $(this)
            .closest('.message')
            .transition('fade')
        ;
    })
;

$('.ui.checkbox')
    .checkbox()
;

$(document)
    .ready(function() {
        $('#find-ipad')
            .form({
                onSuccess: submitForm,
                fields: {
                    serial: {
                        identifier  : 'serial',
                        rules: [
                            {
                                type   : 'empty',
                                prompt : '请输入iPad序列号'
                            }
                        ]
                    }
                }
            })
        ;
    })
;