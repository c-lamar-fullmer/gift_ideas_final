"use strict"; // Enforce strict mode to catch common coding errors and prevent unsafe actions

// Wait for the DOM to fully load before executing the script
document.addEventListener("DOMContentLoaded", function () {
    // Select all forms with the class "delete-form"
    let deleteForms = document.querySelectorAll("form.delete-form");

    // Loop through each delete form
    deleteForms.forEach(form => {
        // Add a "submit" event listener to each form
        form.addEventListener("submit", function (event) {
            // Prevent the default form submission behavior
            event.preventDefault();
            // Stop the event from propagating further
            event.stopPropagation();

            // Display a confirmation dialog to the user
            if (confirm("Are you sure you want to delete this person? This action cannot be undone.")) {
                // If the user confirms, submit the form
                event.target.submit();
            }
        });
    });
});
