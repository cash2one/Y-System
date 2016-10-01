// customize-reset-password-request.js

$(document)
    .ready(function() {
        $('.ui.form')
            .form({
                onSuccess: submitForm,
                fields: {
                    email: {
                        identifier  : 'email',
                        rules: [
                            {
                                type   : 'empty',
                                prompt : '请输入您的电子邮箱地址'
                            },
                            {
                                type   : 'email',
                                prompt : '请输入一个有效的电子邮箱地址'
                            }
                        ]
                    }
                }
            })
        ;
    })
;