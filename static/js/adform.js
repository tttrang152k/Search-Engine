$(document).ready(function () {
    $('#keywords').chips({
        placeholder: 'Enter keyword(s)',
        secondaryPlaceholder: '+Tag',
    });
    $("#adForm").submit((e) => {
        e.preventDefault();
        let instance = M.Chips.getInstance($("#keywords"));
        console.log({title: $("#adTitle").val(), site: $("#adWSite").val(), cpc: $("#adCPC").val(), body: $("#adBody").val(), keywords: $(instance)[0].chipsData})
        $.post("/ads", {title: $("#adTitle").val(), site: $("#adWSite").val(), cpc: $("#adCPC").val(), body: $("#adBody").val(), keywords: $(instance)[0].chipsData})
            .done(function (data) {
                document.getElementById("status").innerHTML = "Success!";
                window.location.replace("/");
            })
            .fail(function(e) {
                console.log(e);
                document.getElementById("status").innerHTML = e.responseText;
            });
    });
});