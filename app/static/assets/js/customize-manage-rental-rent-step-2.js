// customize-manage-rental-rent-step-2.js

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