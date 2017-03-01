$(document).ready(function(){
    // This function enables/disables manual controls if control switch is off/on
    $.getJSON('R1/Current', function(result){ // Get Data
        $.each(result, function(key, val){  // loop through control loop switch
            // build id of manual & switch control form id given a loop switch id
            var manformstr = key.concat('_Manual');
            var switchformstr = key.concat('_Switch');
            var switchval = val[switchformstr]
            $(switchformstr).prop('checked', switchval);
            console.log(val)
            if (switchval){
                $(val).each(function(){ // loop through manual control form fields
                    // disable all manual control form fields
                    $(this).attr("disabled", true)
                });
            }
            else{
                $('#'+manformstr).filter(':input').each(function(){
                    // otherwise enable all manual control form fields
                    $(this).attr("disabled", false)
                });
            };
        });
    });
    setInterval(
        function () {
            $.getJSON('R1/Current', function(result){
                $.each(result, function(key, val){  // loop through control loop switch
                    var switchformstr = key.concat('_Switch');
                    var switchval = val[switchformstr]
                    if (switchval){
                    }
                    else {

                    };
                });
            });
        )
    100);

    // This function automatically send the control on/off function if any control loop switch is clicked.
    $("*[id*=control_on]:visible").click(function(event){ //
        $(event.target.form).submit();
    });
});