$(document).ready(function () {
    $("#loginForm").submit((e) => {
        e.preventDefault();
        $.post("/login", $("#loginForm").serialize())
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