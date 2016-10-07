// customize-manage-rental-rent-step-3.js

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
        $('#confirm-ipad')
            .form({
                onSuccess: submitForm,
                fields: {
                    root: {
                        identifier  : 'root',
                        rules: [
                            {
                                type   : 'checked',
                                prompt : '请确认引导式访问状态正常'
                            }
                        ]
                    },
                    battery: {
                        identifier  : 'battery',
                        rules: [
                            {
                                type   : 'checked',
                                prompt : '请确认电量充足'
                            }
                        ]
                    },
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