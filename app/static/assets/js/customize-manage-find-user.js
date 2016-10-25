// customize-manage-find-user.js

$('select.dropdown')
  .dropdown()
;

$('table')
    .tablesort()
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
        $('#find-user')
            .form({
                onSuccess: submitForm,
                fields: {
                    name_or_email: {
                        identifier  : 'name_or_email',
                        rules: [
                            {
                                type   : 'empty',
                                prompt : '请输入您的电子邮箱地址'
                            }
                        ]
                    }
                }
            })
        ;
    })
;