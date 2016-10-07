// customize-manage-schedule.js

$('select.dropdown')
  .dropdown()
;

$('.ui.checkbox')
  .checkbox()
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
        $('.ui.form')
            .form({
                onSuccess: submitForm,
                fields: {
                    period: {
                        identifier  : 'period',
                        rules: [
                            {
                                type   : 'empty',
                                prompt : '请选择预约时段'
                            }
                        ]
                    },
                    quota: {
                        identifier  : 'quota',
                        rules: [
                            {
                                type   : 'empty',
                                prompt : '请输入预约名额'
                            },
                            {
                                type   : 'integer[1..]',
                                prompt : '请输入一个大于0的整数'
                            }
                        ]
                    }
                }
            })
        ;
    })
;