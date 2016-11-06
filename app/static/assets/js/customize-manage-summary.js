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
    var url = '//' + window.location.hostname + ':' + window.location.port + '/manage/summary/ipad/room/' + roomID;
    $.getJSON(url, function(data) {
        for (var i in data.ipads) {
            $('#ipads')
                .append(
                    $('<div>')
                        .addClass(iPadStates[data.ipads[i].state.color])
                        .addClass('card')
                        .append(
                            $('<div>')
                                .addClass('ipad-basic-info content')
                                .append(
                                    $('<div>')
                                        .addClass('header')
                                        .append(
                                            $('<span>')
                                                .text(data.ipads[i].alias)
                                        )
                                        .append(
                                            $('<span>')
                                                .addClass('right floated')
                                                .text(data.ipads[i].state.display)
                                        )
                                )
                                .append(
                                    $('<div>').addClass('meta')
                                        .append(
                                            $('<code>')
                                                .text(data.ipads[i].serial)
                                        )
                                        .append(
                                            $('<span>')
                                                .addClass('right floated')
                                                .text(data.ipads[i].capacity)
                                        )
                                )
                        )
                        .append(
                            $('<div>')
                                .addClass('content')
                        )
                        .append(
                            $('<div>')
                                .addClass('extra content')
                        )
                );
        };
    });
};
updateCards();
setInterval(updateCards, 15000);