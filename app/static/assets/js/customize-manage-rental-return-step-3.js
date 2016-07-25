// customize-manage-rental-return-step-3.js

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