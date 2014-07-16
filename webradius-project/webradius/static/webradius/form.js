function changeField(name, hide) {
	var name1 = "#" + name
	if (hide)
		$(name1).parent().hide()
	else
		$(name1).parent().show()
}

function changeAllStatic(hide) {
	changeField("id_static_standalone", hide)
	changeField("id_static_ip", hide)
	changeField("id_mask", hide)
	changeField("id_router_address", hide)
	changeField("id_dns_server", hide)
	changeField("id_domain_name", hide)
	changeField("id_rev_domain_name", hide)
	changeField("id_next_server", hide)
	changeField("id_root_path", hide)
	changeField("id_boot_filename", hide)
	changeField("id_full_access", hide)
	changeField("id_netbios_name_server", hide)
	changeField("id_netbios_name_server2", hide)
	changeField("id_netbios_node_type", hide)
	changeField("id_pool", !hide)	
}

function changeAllStandalone(hide) {
	changeField("id_mask", hide)
	changeField("id_router_address", hide)
	changeField("id_dns_server", hide)
	changeField("id_domain_name", hide)
	changeField("id_rev_domain_name", hide)
	changeField("id_next_server", hide)
	changeField("id_root_path", hide)
	changeField("id_boot_filename", hide)
	changeField("id_netbios_name_server", hide)
	changeField("id_netbios_name_server2", hide)
	changeField("id_netbios_node_type", hide)
	changeField("id_pool", !hide)
}

function showOrHideFields() {
	if ($("#id_static").is(":checked")) {
		changeAllStatic(false)
		
		if ($("#id_static_standalone").is(":checked")) {
			changeAllStandalone(false)
		} else {
			changeAllStandalone(true)
		}
	} else {
		changeAllStatic(true)
	}
}

$(document).ready(function() {
	var myControl=  {
		create: function(tp_inst, obj, unit, val, min, max, step){
			$('<input class="ui-timepicker-input" value="' + val + '" style="width:50%">')
				.appendTo(obj)
				.spinner({
					min: min,
					max: max,
					step: step,
					change: function(e,ui){ // key events
							// don't call if api was used and not key press
							if(e.originalEvent !== undefined)
								tp_inst._onTimeChange();
							tp_inst._onSelectHandler();
						},
					spin: function(e,ui){ // spin events
							tp_inst.control.value(tp_inst, obj, unit, ui.value);
							tp_inst._onTimeChange();
							tp_inst._onSelectHandler();
						}
				});
			return obj;
		},
		options: function(tp_inst, obj, unit, opts, val){
			if(typeof(opts) == 'string' && val !== undefined)
					return obj.find('.ui-timepicker-input').spinner(opts, val);
			return obj.find('.ui-timepicker-input').spinner(opts);
		},
		value: function(tp_inst, obj, unit, val){
			if(val !== undefined)
				return obj.find('.ui-timepicker-input').spinner('value', val);
			return obj.find('.ui-timepicker-input').spinner('value');
		}
	};
	
	$('.date_time_input').datetimepicker({
		controlType: myControl,
		dateFormat: "dd-mm-yy",
		timeFormat: "hh:mm"
	});

	showOrHideFields()
});

$(function() {
	$("#id_static").change(function() {
		showOrHideFields()
	});
	$("#id_static_standalone").change(function() {
		showOrHideFields()
	});	
});

$(function() {
	$('#id_mac').keypress(function(){
    	var macval = $('#id_mac').setMask('**-**-**-**-**-**').val();
    	macval = macval.replace(/([^0-9a-fA-F\-])|\s/g,'').toLowerCase();
    	$('#id_mac').attr('value' , macval); 
    });
});