 $(document).ready(function(){     
	 
        jQuery(".tabsui").tabs();
        jQuery("#ajax-indicator").ajaxStart(function() {  $(this).show(); });
     	jQuery("#ajax-indicator").ajaxStop(function() { $(this).hide(); });

        jQuery("#nav li").hover(
            function () {
               $(this).addClass('hover').attr('class','hover');
             }, 
             function () {
               $(this).removeClass('hover');
             }
        );

        jQuery.event.add(window, "load", resizeFrame);
        jQuery.event.add(window, "resize", resizeFrame);

        function resizeFrame() {
            var h = $(window).height();
            var w = $(window).width();
            jQuery("#content-main").css('min-height',(h < 1024) ? 400 : 100);
        }

		setTimeout(function() {
	        $(".messagelist").hide('blind', {}, 500)
	    }, 5000);
	    
	    $("button").button();
		$('input[type=submit]').button();
});
    