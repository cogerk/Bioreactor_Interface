$(document).ready(function(){
    $("#signal").on('change', function() {
    // This function gets current slopes/ints of a signal and returns it to form when a new signal is selected
        // Current values are sent from server on page load as {#slopes#} & {#ints#}
        // This converts that dictionary of current values to js dict
        js_ints = {{ ints|tojson|safe }}
        js_slopes = {{ slopes|tojson|safe }}
        js_graphs = {{ scripts|tojson|safe }}

        // Change values
        $("#slope").val(js_graphs[this.value]);
        $("#intercept").val(js_ints[this.value]);
        $('#graph).html(js_graphs[this.value]);
    });
});