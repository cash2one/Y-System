// customize-reset-password.js

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
                    },
                    password: {
                        identifier  : 'password',
                        rules: [
                            {
                                type   : 'empty',
                                prompt : '请设置您的新密码'
                            },
                            {
                                type   : 'length[6]',
                                prompt : '密码长度至少为6位'
                            }
                        ]
                    },
                    password2: {
                        identifier  : 'password2',
                        rules: [
                            {
                                type   : 'empty',
                                prompt : '请再次输入您的新密码'
                            },
                            {
                                type   : 'match[password]',
                                prompt : '两次设置的新密码不一致'
                            }
                        ]
                    }
                }
            })
        ;
    })
;