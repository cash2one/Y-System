// customize-manage-edit-user.js

$('select.dropdown')
  .dropdown()
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
        $('#edit-user')
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
                    role: {
                        identifier  : 'role',
                        rules: [
                            {
                                type   : 'empty',
                                prompt : '请选择用户组'
                            }
                        ]
                    }
                }
            })
        ;
    })
;