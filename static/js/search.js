let facts = [`Every year over one million earthquakes shake the Earth.`,
`When Krakatoa erupted in 1883, its force was so great it could be heard 4,800 kilometres away in Australia.`,
`The largest ever hailstone weighed over 1kg and fell in Bangladesh in 1986.`,
`Every second around 100 lightning bolts strike the Earth.`,
`Every year lightning kills 1000 people.`,
`In October 1999 an Iceberg the size of London broke free from the Antarctic ice shelf .`,
`If you could drive your car straight up you would arrive in space in just over an hour.`,
`Human tapeworms can grow up to 22.9m.`];
let searchWord = "";
// Custom implementation of waiting until the user stops typing before calling a setTimeout event from one of my older projects -Tim
let delay = (() => {
    var timer = 0;
    return (callback, ms, that) => {
        clearTimeout(timer);
        timer = setTimeout(callback.bind(that), ms);
    };
})();

function search() {
    console.log("searching");
    while (document.getElementById("searchresults").hasChildNodes()) {
        document.getElementById("searchresults").removeChild(document.getElementById("searchresults").lastChild);
    }
    $.get("/query/" + searchWord, (data) => {
        data.forEach(d => createOption(d));
    });
}

function createOption(d) {
    let option = document.createElement("option");
    option.value = d;
    document.getElementById("searchresults").appendChild(option);
}
// Some JQuery functions do not work with ES6 syntax for some reason
$(document).ready(function () {
    if (document.getElementById("dailyfacts")) {
        document.getElementById("dailyfacts").innerHTML = facts[Math.floor(Math.random() * (facts.length - 0) + 0)];
    }
    
    $('#searchbar').keyup(function () {
        let inputText = $(this).val();
        delay(() => {
            searchWord = inputText;
            search();
        }, 1000);

    });
    $('#searchbutton').click(function () {
        window.location.replace("/search/" + $("#searchbar").val());
    });
    $('#searchbar').keypress(function(e){
        if(e.which == 13) {
            $('#searchbutton').click();
        }
    });
});