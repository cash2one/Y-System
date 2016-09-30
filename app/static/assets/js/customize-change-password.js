// customize-change-password.js

function submitForm() {
    $(this).form('submit');
};

$(document)
    .ready(function() {
        $('.ui.form')
            .form({
                onSuccess: submitForm,
                fields: {
                    old_password: {
                        identifier  : 'old_password',
                        rules: [
                            {
                                type   : 'empty',
                                prompt : '请设输入您的旧密码'
                            },
                            {
                                type   : 'length[6]',
                                prompt : '密码长度至少为6位'
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
                                type   : 'different[old_password]',
                                prompt : '新密码与旧密码相同'
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