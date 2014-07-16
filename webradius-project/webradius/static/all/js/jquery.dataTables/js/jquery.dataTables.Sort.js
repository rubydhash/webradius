$(document).ready(function(){
jQuery.fn.dataTableExt.oSort['uk_date-asc']  = function(a,b) {
	var ukDatea = a.split('/');
	var ukDateb = b.split('/');
	
	var x = (ukDatea[2] + ukDatea[1] + ukDatea[0]) * 1;
	var y = (ukDateb[2] + ukDateb[1] + ukDateb[0]) * 1;
	
	return ((x < y) ? -1 : ((x > y) ?  1 : 0));
};

jQuery.fn.dataTableExt.oSort['uk_date-desc'] = function(a,b) {
	var ukDatea = a.split('/');
	var ukDateb = b.split('/');
	
	var x = (ukDatea[2] + ukDatea[1] + ukDatea[0]) * 1;
	var y = (ukDateb[2] + ukDateb[1] + ukDateb[0]) * 1;
	
	return ((x < y) ? 1 : ((x > y) ?  -1 : 0));
};

jQuery.fn.dataTableExt.oSort['ip-address-asc']  = function(a,b) {
	var m = a.split("."), x = "";
	var n = b.split("."), y = "";
	for(var i = 0; i < m.length; i++) {
		var item = m[i];
		if(item.length == 1) {
			x += "00" + item;
		} else if(item.length == 2) {
			x += "0" + item;
		} else {
			x += item;
		}
	}
	for(var i = 0; i < n.length; i++) {
		var item = n[i];
		if(item.length == 1) {
			y += "00" + item;
		} else if(item.length == 2) {
			y += "0" + item;
		} else {
			y += item;
		}
	}
	return ((x < y) ? -1 : ((x > y) ? 1 : 0));
};

jQuery.fn.dataTableExt.oSort['ip-address-desc']  = function(a,b) {
	var m = a.split("."), x = "";
	var n = b.split("."), y = "";
	for(var i = 0; i < m.length; i++) {
		var item = m[i];
		if(item.length == 1) {
			x += "00" + item;
		} else if (item.length == 2) {
			x += "0" + item;
		} else {
			x += item;
		}
	}
	for(var i = 0; i < n.length; i++) {
		var item = n[i];
		if(item.length == 1) {
			y += "00" + item;
		} else if (item.length == 2) {
			y += "0" + item;
		} else {
			y += item;
		}
	}
	return ((x < y) ? 1 : ((x > y) ? -1 : 0));
};


function trim(str) {
	str = str.replace(/^\s+/, '');
	for (var i = str.length - 1; i >= 0; i--) {
		if (/\S/.test(str.charAt(i))) {
			str = str.substring(0, i + 1);
			break;
		}
	}
	return str;
}

jQuery.fn.dataTableExt.oSort['date-euro-asc'] = function(a, b) {
	if (trim(a) != '') {
		var frDatea = trim(a).split(' ');
		var frTimea = frDatea[1].split(':');
		var frDatea2 = frDatea[0].split('/');
		var x = (frDatea2[2] + frDatea2[1] + frDatea2[0] + frTimea[0] + frTimea[1] + frTimea[2]) * 1;
	} else {
		var x = 10000000000000; // = l'an 1000 ...
	}

	if (trim(b) != '') {
		var frDateb = trim(b).split(' ');
		var frTimeb = frDateb[1].split(':');
		frDateb = frDateb[0].split('/');
		var y = (frDateb[2] + frDateb[1] + frDateb[0] + frTimeb[0] + frTimeb[1] + frTimeb[2]) * 1;		                
	} else {
		var y = 10000000000000;		                
	}
	var z = ((x < y) ? -1 : ((x > y) ? 1 : 0));
	return z;
};

jQuery.fn.dataTableExt.oSort['date-euro-desc'] = function(a, b) {
	if (trim(a) != '') {
		var frDatea = trim(a).split(' ');
		var frTimea = frDatea[1].split(':');
		var frDatea2 = frDatea[0].split('/');
		var x = (frDatea2[2] + frDatea2[1] + frDatea2[0] + frTimea[0] + frTimea[1] + frTimea[2]) * 1;		                
	} else {
		var x = 10000000000000;		                
	}

	if (trim(b) != '') {
		var frDateb = trim(b).split(' ');
		var frTimeb = frDateb[1].split(':');
		frDateb = frDateb[0].split('/');
		var y = (frDateb[2] + frDateb[1] + frDateb[0] + frTimeb[0] + frTimeb[1] + frTimeb[2]) * 1;		                
	} else {
		var y = 10000000000000;		                
	}		            
	var z = ((x < y) ? 1 : ((x > y) ? -1 : 0));		            
	return z;
};

jQuery.fn.dataTableExt.oSort['formatted-num-asc'] = function(x,y){
 x = x.replace(/[^\d\-\.\/]/g,'');
 y = y.replace(/[^\d\-\.\/]/g,'');
 if(x.indexOf('/')>=0)x = eval(x);
 if(y.indexOf('/')>=0)y = eval(y);
 return x/1 - y/1;
}
jQuery.fn.dataTableExt.oSort['formatted-num-desc'] = function(x,y){
 x = x.replace(/[^\d\-\.\/]/g,'');
 y = y.replace(/[^\d\-\.\/]/g,'');
 if(x.indexOf('/')>=0)x = eval(x);
 if(y.indexOf('/')>=0)y = eval(y);
 return y/1 - x/1;
}


});

