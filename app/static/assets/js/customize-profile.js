// customize-profile.js

$('.message .close')
    .on('click', function() {
        $(this)
            .closest('.message')
            .transition('fade')
        ;
    })
;

$('table')
    .tablesort()
;

$('.ui.search')
    .search({
        apiSettings: {
            url: '//' + window.location.hostname + ':' + window.location.port + '/manage/search/user/?keyword={query}'
        },
        // selectFirstResult: true,
        showNoResults: false
    })
;