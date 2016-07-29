// customize-manage-period.js

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