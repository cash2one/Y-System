// customize.js

$(document)
  .ready(function() {

    // fix menu when passed
    $('.masthead')
      .visibility({
        once: false,
        onBottomPassed: function() {
          $('.fixed.menu').transition('fade in');
        },
        onBottomPassedReverse: function() {
          $('.fixed.menu').transition('fade out');
        }
      })
    ;

    // create sidebar and attach to menu open
    $('.ui.sidebar')
      .sidebar('attach events', '.toc.item')
    ;

  })
;

// popup wechat qr code
$('#wechat-qr-code-click')
  .popup({
    popup : $('#wechat-qr-code'),
    on    : 'click'
  })
;

// footer copyright
$('#copyright')
  .html(
   function(){
     var date = new Date();
     return '<i class="copyright icon"></i> 2011-' +  date.getFullYear() + ' 北京云英一语教育咨询有限公司 版权所有';
   }
  )
;