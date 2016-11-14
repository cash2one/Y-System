// customize-manage-summary.js

$('.message .close')
    .on('click', function() {
        $(this)
            .closest('.message')
            .transition('fade')
        ;
    })
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
                        .attr('id', 'ipad-' + i)
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
                                                .attr('id', 'ipad-state-' + i)
                                                .addClass('right floated')
                                        )
                                )
                                .append(
                                    $('<div>')
                                        .addClass('meta')
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
                                .attr('id', 'ipad-content-' + i)
                                .addClass('center aligned content')
                                .append(
                                    $('<div>')
                                        .addClass('ui statistic')
                                        .append(
                                            $('<div>')
                                                .addClass('value')
                                        )
                                        .append(
                                            $('<div>')
                                                .addClass('label')
                                                .text(data.ipads[i].state)
                                        )
                                )
                        )
                        .append(
                            $('<div>')
                                .addClass('extra content')
                                .append(
                                    $('<span>')
                                        .append(moment(data.ipads[i].last_modified_at, 'YYYY-MM-DDTh:mm:ssZ').fromNow() + ' [' + data.ipads[i].last_modified_by + ']')
                                )
                                .append(
                                    $('<span>')
                                        .attr('id', 'ipad-battery-' + i)
                                        .addClass('right floated')
                                )
                        )
                );
            if (data.ipads[i].state == '待机') {
                // $('#ipad-' + i).addClass('grey');
                $('#ipad-state-' + i).html('<i class="wait icon"></i>' + data.ipads[i].state);
                $('#ipad-content-' + i + ' .statistic').addClass('grey');
                $('#ipad-content-' + i + ' .value').html('<i class="wait icon"></i>');
            } else if (data.ipads[i].state == '借出') {
                $('#ipad-battery-' + i).html(data.ipads[i].battery_life.percent + '% <i class="' + data.ipads[i].battery_life.level + ' battery icon"></i>');
                if (data.ipads[i].now_rented_by.last_punch.course_type == 'VB') {
                    $('#ipad-' + i).addClass('blue');
                    $('#ipad-state-' + i).append(
                        $('<a>')
                            .attr('href', data.ipads[i].now_rented_by.url)
                            .attr('target', '_blank')
                            .html('<i class="user icon"></i>' + data.ipads[i].now_rented_by.name)
                    );
                    $('#ipad-content-' + i + ' .statistic').addClass('blue');
                    $('#ipad-content-' + i + ' .value').text(data.ipads[i].now_rented_by.last_punch.course_type);
                    $('#ipad-content-' + i + ' .label').text(data.ipads[i].now_rented_by.last_punch.alias);
                } else if (data.ipads[i].now_rented_by.last_punch.course_type == 'Y-GRE') {
                    $('#ipad-' + i).addClass('teal');
                    $('#ipad-state-' + i).append(
                        $('<a>')
                            .attr('href', data.ipads[i].now_rented_by.url)
                            .attr('target', '_blank')
                            .html('<i class="user icon"></i>' + data.ipads[i].now_rented_by.name)
                    );
                    $('#ipad-content-' + i + ' .statistic').addClass('teal');
                    $('#ipad-content-' + i + ' .value').text(data.ipads[i].now_rented_by.last_punch.course_type);
                    $('#ipad-content-' + i + ' .label').text(data.ipads[i].now_rented_by.last_punch.lesson);
                } else {
                    $('#ipad-' + i).addClass('yellow');
                    $('#ipad-state-' + i).html('<i class="upload icon"></i>' + data.ipads[i].state);
                    $('#ipad-content-' + i + ' .statistic').addClass('yellow');
                    $('#ipad-content-' + i + ' .value').html('<i class="upload icon"></i>');
                };
                if (data.ipads[i].battery_life.percent < 20) {
                    $('#ipad-' + i).removeClass('blue teal').addClass('orange');
                    $('#ipad-content-' + i + ' .statistic').removeClass('blue teal').addClass('orange');
                    $('#ipad-content-' + i + ' .value').html('<i class="empty battery icon"></i>');
                    if (data.ipads[i].now_rented_by.last_punch.course_type == 'VB') {
                        $('#ipad-content-' + i + ' .label').text(data.ipads[i].now_rented_by.last_punch.alias2);
                    } else if (data.ipads[i].now_rented_by.last_punch.course_type == 'Y-GRE') {
                        $('#ipad-content-' + i + ' .label').text(data.ipads[i].now_rented_by.last_punch.alias3);
                    };
                };
            } else if (data.ipads[i].state == '候补') {
                $('#ipad-' + i).addClass('grey');
                $('#ipad-state-' + i).html('<i class="cube icon"></i>' + data.ipads[i].state);
                $('#ipad-content-' + i + ' .statistic').addClass('grey');
                $('#ipad-content-' + i + ' .value').html('<i class="cube icon"></i>');
            } else if (data.ipads[i].state == '维护') {
                $('#ipad-' + i).addClass('red');
                $('#ipad-state-' + i).html('<i class="configure icon"></i>' + data.ipads[i].state);
                $('#ipad-content-' + i + ' .statistic').addClass('red');
                $('#ipad-content-' + i + ' .value').html('<i class="configure icon"></i>');
            } else if (data.ipads[i].state == '充电') {
                $('#ipad-' + i).addClass('green');
                $('#ipad-state-' + i).html('<i class="lightning icon"></i>' + data.ipads[i].state);
                $('#ipad-content-' + i + ' .statistic').addClass('green');
                $('#ipad-content-' + i + ' .value').html('<i class="lightning icon"></i>');
            } else if (data.ipads[i].state == '退役') {
                $('#ipad-' + i).addClass('olive');
                $('#ipad-state-' + i).html('<i class="recycle icon"></i>' + data.ipads[i].state);
                $('#ipad-content-' + i + ' .statistic').addClass('olive');
                $('#ipad-content-' + i + ' .value').html('<i class="recycle icon"></i>');
            };
        };
    });
};
updateCards();
setInterval(updateCards, 15000);