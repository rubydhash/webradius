$(document).ready(function(){
   
    $('.cpf_field').setMask('999.999.999-99');
    $('.rg_field').setMask('99999999999999999999999999');
    $('.cnpj_field').setMask('99.999.999/9999-99');
    $('.cep_field').setMask('99999-999');
    
    $('int_field').setMask('99999999999999999999');
    
    $('.mac_field').keypress(function(){
         var macval = $('.mac').setMask('**:**:**:**:**:**').val();
         macval = macval.replace(/([^0-9a-fA-F:])|\s/g,'').toUpperCase();
         $('.mac').attr('value' , macval); 
    });
       
    $('.mac_dhcp_field').keypress(function(){
         var macval = $('.mac_dhcp').setMask('**:**:**:**:**:**').val();
         macval = macval.replace(/([^0-9a-fA-F:])|\s/g,'').toUpperCase();
         $('.mac_dhcp').attr('value' , macval); 
    });
                 
});