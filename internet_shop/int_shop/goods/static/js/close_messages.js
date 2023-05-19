$(document).ready(function() {
   $('.success-message > span:nth-child(1), .error-message > span:nth-child(1)').click(function(){
       $(this).parent().css('visibility', 'hidden'); //скрытие всего блока с сообщением
   });
});