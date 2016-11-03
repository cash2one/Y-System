// customize-manage-ipad.js

$('.message .close')
    .on('click', function() {
        $(this)
            .closest('.message')
            .transition('fade')
        ;
    })
;

$('select.dropdown')
    .dropdown()
;

$('table')
    .tablesort()
;

$(document)
    .ready(function() {
        $('#new-ipad')
            .form({
                onSuccess: submitForm,
                fields: {
                    alias: {
                        identifier  : 'alias',
                        rules: [
                            {
                                type   : 'empty',
                                prompt : '请填写iPad编号'
                            }
                        ]
                    },
                    serial: {
                        identifier  : 'serial',
                        rules: [
                            {
                                type   : 'empty',
                                prompt : '请填写iPad序列号'
                            },
                            {
                                type   : 'exactLength[12]',
                                prompt : 'iPad序列号必须为12位'
                            }
                        ]
                    }
                }
            })
        ;
    })
;