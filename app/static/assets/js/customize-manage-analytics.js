// customize-manage-analytics.js

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

$('#analytics-iframe')
    .load(function() {
        var analyticsDashboardHeight = $(this).contents().find('body').height();
        $(this).height(analyticsDashboardHeight);
    })
;