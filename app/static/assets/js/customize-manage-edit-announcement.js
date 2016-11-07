// customize-manage-edit-announcement.js

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
        $('#edit-announcement')
            .form({
                onSuccess: submitForm,
                fields: {
                    title: {
                        identifier  : 'title',
                        rules: [
                            {
                                type   : 'empty',
                                prompt : '请输入通知标题'
                            }
                        ]
                    },
                    body: {
                        identifier  : 'body',
                        rules: [
                            {
                                type   : 'empty',
                                prompt : '请输入通知内容'
                            }
                        ]
                    }
                }
            })
        ;
    })
;