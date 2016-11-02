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

$('.ui.search')
    .search({
        apiSettings: {
            url: '//' + window.location.hostname + ':' + window.location.port + '/manage/suggest/user/?keyword={query}'
        },
        // selectFirstResult: true,
        showNoResults: false
    })
;