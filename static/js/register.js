$(document).ready(function () {
    $("#regForm").submit((e) => {
        e.preventDefault();
        if ($("#regPassword").val() != $("#cregPassword").val()) {
            document.getElementById("status").innerHTML = "Passwords do not match!";
            return false;
        }
        console.log($("#regForm").serialize());
        $.post("/register", $("#regForm").serialize())
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