// customize-manage-rental-return-step-1-alt.js

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
        $('#find-user')
            .form({
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