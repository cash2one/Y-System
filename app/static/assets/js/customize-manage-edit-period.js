// customize-manage-edit-period.js

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
        $('#edit-period')
            .form({
                onSuccess: submitForm,
                fields: {
                    name: {
                        identifier  : 'name',
                        rules: [
                            {
                                type   : 'empty',
                                prompt : '请填写时段名称'
                            }
                        ]
                    }
                }
            })
        ;
    })
;