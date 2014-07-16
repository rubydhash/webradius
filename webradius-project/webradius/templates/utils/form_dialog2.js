{% load i18n %}
<script type="text/javascript" charset="utf-8">
     $(document).ready(function(){

		$('#formdialog').dialog({
		    {% if form.errors or object %} 
			    autoOpen: true,
			{% else %}
			    autoOpen: false,
            {% endif %}
			width: {{widthset}},
			{% if heightset %}
			height: {{ heightset }},
		    {% endif %}
			buttons: {
				"{% trans 'Alterar' %}": function() { 
					$('#formdialogdata').submit(); 
				}, 
				"{% trans 'Cancelar' %}": function() { 
					$(this).dialog("close"); 
				} 
			},
			modal: true,
			close: function(event, ui) {  window.location='{{urlget}}'; }
		});
		
		$('#formdialog input').keypress(function(e) { 
           if ((e.which && e.which == 13 ) || (e.keyCode && e.keyCode == 13)) { 
               $('#formdialogdata').submit(); 
           }
        });	
        
         $('#linkadd').click(function() { 
             $('#formdialog').dialog('open');
             return false;
         });
                     
    });
</script>
