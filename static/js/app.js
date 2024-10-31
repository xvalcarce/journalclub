let startDate = "{{ start_date }}";
const endDate = "{{ end_date }}";

// Show the add-paper-form modal
$("#add-paper-trigger").on("click", function() {
    $("#add-paper-modal").show();
});

// Hide the add-paper-form modal
$("#close-form").on("click", function() {
    $("#add-paper-modal").hide();
});

// Submit the add paper form and reload
$("#add-paper-form").on("submit", function(event) {
    event.preventDefault();
    const formData = $(this).serialize();
    $.post("/add-paper/", formData, function(response) {
        alert(response.message);
        location.reload();
    }).fail(function(xhr) {
        alert(xhr.responseJSON.detail);
    });
});

// Handle upvote button click
$(".upvote-button").on("click", function() {
    const doi = $(this).data("doi");
    const button = $(this);
    $.post("/upvote/", { doi: doi }, function(response) {
        button.prop("disabled", true).text("Voted");
        const votesElement = $("#votes-" + doi);
        const currentVotes = parseInt(votesElement.text().replace("Votes: ", ""));
        votesElement.text("Votes: " + (currentVotes + 1));
    }).fail(function(xhr) {
        alert(xhr.responseJSON.detail);
    });
});

