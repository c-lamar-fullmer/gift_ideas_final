"use strict";
document.addEventListener("DOMContentLoaded", function () {
    let deleteForms = document.querySelectorAll("form.delete-form");

    deleteForms.forEach(form => {
        form.addEventListener("submit", function (event) {
            event.preventDefault();
            event.stopPropagation();

            if (confirm("Are you sure you want to delete this person? This action cannot be undone.")) {
                event.target.submit();
            }
        });
    });
});
