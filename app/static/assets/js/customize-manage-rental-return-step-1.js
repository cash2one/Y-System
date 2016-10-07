// customize-manage-rental-return-step-1.js

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
        $('#find-ipad')
            .form({
                onSuccess: submitForm,
                fields: {
                    volume: {
                        identifier  : 'volume',
                        rules: [
                            {
                                type   : 'checked',
                                prompt : '请确认音量已经复位'
                            }
                        ]
                    },
                    brightness: {
                        identifier  : 'brightness',
                        rules: [
                            {
                                type   : 'checked',
                                prompt : '请确认亮度已经复位'
                            }
                        ]
                    },
                    playback_speed: {
                        identifier  : 'playback_speed',
                        rules: [
                            {
                                type   : 'checked',
                                prompt : '请确认播放速度已经复位'
                            }
                        ]
                    },
                    show_menu: {
                        identifier  : 'show_menu',
                        rules: [
                            {
                                type   : 'checked',
                                prompt : '请确认画面停留在目录状态'
                            }
                        ]
                    },
                    clean: {
                        identifier  : 'clean',
                        rules: [
                            {
                                type   : 'checked',
                                prompt : '请确认屏幕已清洁'
                            }
                        ]
                    },
                    serial: {
                        identifier  : 'serial',
                        rules: [
                            {
                                type   : 'empty',
                                prompt : '请输入iPad序列号'
                            }
                        ]
                    },
                }
            })
        ;
    })
;