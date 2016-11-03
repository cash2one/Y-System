// customize-manage-edit-activation.js

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

$(document)
    .ready(function() {
        $('#edit-activation')
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
                    },
                    role: {
                        identifier  : 'role',
                        rules: [
                            {
                                type   : 'empty',
                                prompt : '请选择用户组'
                            }
                        ]
                    },
                    vb_course: {
                        identifier  : 'vb_course',
                        rules: [
                            {
                                type   : 'empty',
                                prompt : '请选择VB班级'
                            }
                        ]
                    }
                }
            })
        ;
    })
;