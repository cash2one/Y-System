// customize-manage-rental-return-step-1-alt.js

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

$('.ui.search')
    .search({
        apiSettings: {
            url: '//' + window.location.hostname + ':' + window.location.port + '/manage/suggest/email/?keyword={query}'
        },
        showNoResults: false
    })
;