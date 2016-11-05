// customize-manage-summary.js

$('.message .close')
    .on('click', function() {
        $(this)
            .closest('.message')
            .transition('fade')
        ;
    })
;

$('.ui.accordion')
    .accordion()
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

// update iPad info
var iPadStates = {
    '待机': 'blue',
    '借出': 'yellow',
    'VB': 'teal',
    'Y-GRE': 'orange',
    '候补': 'black',
    '维护': 'red',
    '充电': 'green',
    '退役': 'grey',
};
function updateCards() {
    $('.card')
        .each(function() {
            var iPadID = $(this).attr('id').replace('ipad-', '');
            var url = '//' + window.location.hostname + ':' + window.location.port + '/manage/info/ipad/' + iPadID;
            $.getJSON(url, function(data) {
                $('#ipad-' + iPadID)
                    .removeClass('red orange yellow olive green teal blue violet purple pink brown grey black')
                    .addClass(iPadStates[data.state.color]);
                $('#ipad-alias-' + iPadID)
                    .text(data.alias);
                $('#ipad-state-' + iPadID)
                    .text(data.state.display);
                $('#ipad-serial-' + iPadID)
                    .text(data.serial);
                $('#ipad-capacity-' + iPadID)
                    .text(data.capacity);
            });
        });
};
updateCards();
setInterval(updateCards, 15000);