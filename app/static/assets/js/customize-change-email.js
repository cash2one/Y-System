// customize-change-email.js

function submitForm() {
    $(this).form('submit');
};

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
                                prompt : '请输入您的新电子邮箱地址'
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
                                prompt : '请设置您的密码'
                            },
                            {
                                type   : 'length[6]',
                                prompt : '密码长度至少为6位'
                            }
                        ]
                    }
                }
            })
        ;
    })
;