// customize-activate.js

$('.ui.checkbox')
    .checkbox()
;

$(document)
    .ready(function() {
        $('.ui.form')
            .form({
                onSuccess: submitForm,
                fields: {
                    name: {
                        identifier  : 'name',
                        rules: [
                            {
                                type   : 'empty',
                                prompt : '请输入您的姓名'
                            }
                        ]
                    },
                    activation_code: {
                        identifier  : 'activation_code',
                        rules: [
                            {
                                type   : 'empty',
                                prompt : '请输入您的激活码'
                            },
                            {
                                type   : 'length[6]',
                                prompt : '激活码长度至少为6位'
                            }
                        ]
                    },
                    password: {
                        identifier  : 'password',
                        rules: [
                            {
                                type   : 'empty',
                                prompt : '请设置您的密码'
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
                                prompt : '请再次输入您的密码'
                            },
                            {
                                type   : 'match[password]',
                                prompt : '两次设置的密码不一致'
                            }
                        ]
                    },
                    eula: {
                        identifier  : 'eula',
                        rules: [
                            {
                                type   : 'checked',
                                prompt : '请同意云英语服务条款'
                            }
                        ]
                    }
                }
            })
        ;
    })
;