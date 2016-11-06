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
function updateCards() {
    var url = '//' + window.location.hostname + ':' + window.location.port + '/manage/summary/ipad/room/' + roomID;
    $.getJSON(url, function(data) {
        $('.card').remove();
        for (var i in data.ipads) {
            $('#ipads')
                .append(
                    $('<div>')
                        .addClass(data.ipads[i].state.css_color)
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
                                                .text(data.ipads[i].state.html_display)
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