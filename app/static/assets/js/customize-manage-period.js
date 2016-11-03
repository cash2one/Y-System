// customize-manage-period.js

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

$('.ui.checkbox')
    .checkbox()
;

$('table')
    .tablesort()
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
                                prompt : '请输入时段名称'
                            }
                        ]
                    }
                }
            })
        ;
    })
;