// date.js
document.addEventListener("DOMContentLoaded", () => {
    const currentMonthDisplay = document.getElementById("current-month-display");
    let currentDate; // Keep track of the current date for navigation

    // Initialize currentDate based on URL parameters or current date
    const urlParams = new URLSearchParams(window.location.search);
    const yearParam = urlParams.get('year');
    const monthParam = urlParams.get('month');

    if (yearParam && monthParam) {
        currentDate = new Date(parseInt(yearParam), parseInt(monthParam) - 1, 1); // Month is 0-indexed
    } else {
        currentDate = new Date();
    }

    function updateMonthDisplay() {
        const yyyy = currentDate.getFullYear();
        const mm = String(currentDate.getMonth() + 1).padStart(2, '0');
        if (currentMonthDisplay) {
            currentMonthDisplay.textContent = `${yyyy}.${mm}.`;
        }
    }

    // Initialize on page load
    updateMonthDisplay();

    // Make changeDate a global function or attach to window for onclick to work
    window.changeDate = function(offset) {
        currentDate.setMonth(currentDate.getMonth() + offset);
        updateMonthDisplay();

        // Redirect to home view with new year and month parameters
        const year = currentDate.getFullYear();
        const month = String(currentDate.getMonth() + 1).padStart(2, '0');
        window.location.href = `${homeUrl}?year=${year}&month=${month}`;
    };
});