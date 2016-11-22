// customize-manage-edit-ipad.js

$('.message .close')
    .on('click', function() {
        $(this)
            .closest('.message')
            .transition('fade')
        ;
    })
;

$('select.dropdown')
    .dropdown()
;

$(document)
    .ready(function() {
        $('#edit-ipad')
            .form({
                onSuccess: submitForm,
                fields: {
                    alias: {
                        identifier  : 'alias',
                        rules: [
                            {
                                type   : 'empty',
                                prompt : '请填写iPad编号'
                            }
                        ]
                    },
                    serial: {
                        identifier  : 'serial',
                        rules: [
                            {
                                type   : 'empty',
                                prompt : '请填写iPad序列号'
                            },
                            {
                                type   : 'exactLength[12]',
                                prompt : 'iPad序列号必须为12位'
                            }
                        ]
                    },
                    video_playback: {
                        identifier  : 'video_playback',
                        rules: [
                            {
                                type   : 'empty',
                                prompt : '请输入满电量可播放视频时间（小时）'
                            },
                            {
                                type   : 'number',
                                prompt : '满电量可播放视频时间必须为数字'
                            }
                        ]
                    }
                }
            })
        ;
    })
;