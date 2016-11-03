// customize-manage-user.js

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
        $('#new-activation')
            .form({
                onSuccess: submitForm,
                fields: {
                    name: {
                        identifier  : 'name',
                        rules: [
                            {
                                type   : 'empty',
                                prompt : '请填写用户姓名'
                            }
                        ]
                    },
                    activation_code: {
                        identifier  : 'activation_code',
                        rules: [
                            {
                                type   : 'empty',
                                prompt : '请填写激活码'
                            },
                            {
                                type   : 'length[6]',
                                prompt : '激活码至少为6位'
                            }
                        ]
                    }
                }
            })
        ;
    })
;