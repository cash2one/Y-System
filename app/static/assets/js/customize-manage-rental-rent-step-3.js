// customize-manage-rental-rent-step-3.js

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
        $('#confirm-ipad')
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
                    },
                    battery_life: {
                        identifier  : 'battery_life',
                        rules: [
                            {
                                type   : 'empty',
                                prompt : '请输入iPad剩余电量'
                            },
                            {
                                type   : 'integer[0..100]',
                                prompt : '电量数值超出范围（0 ~ 100）'
                            }
                        ]
                    },
                    root: {
                        identifier  : 'root',
                        rules: [
                            {
                                type   : 'checked',
                                prompt : '请确认引导式访问状态正常'
                            }
                        ]
                    }
                }
            })
        ;
    })
;