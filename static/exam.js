
"use strict";

document.addEventListener("DOMContentLoaded", () => {
    const timer = document.getElementById("countdown");
    const form = document.getElementById("exam-form");
    const submitButton = document.getElementById("submit-exam");

    if (!timer || !form || !submitButton) return;

    let remaining = Number(timer.dataset.duration);

    if (!Number.isFinite(remaining) || remaining <= 0) return;

    function updateTimer() {
        const minutes = Math.floor(remaining / 60);
        const seconds = remaining % 60;

        timer.textContent =
            String(minutes).padStart(2, "0") + ":" +
            String(seconds).padStart(2, "0");

        if (remaining <= 60) {
            timer.classList.add("timer-warning");
        }
    }

    updateTimer();

    const interval = window.setInterval(() => {
        remaining -= 1;

        if (remaining <= 0) {
            remaining = 0;
            updateTimer();
            window.clearInterval(interval);

            submitButton.disabled = true;
            submitButton.textContent = "Submitting...";
            form.requestSubmit();
            return;
        }

        updateTimer();
    }, 1000);

    form.addEventListener("submit", () => {
        submitButton.disabled = true;
        submitButton.textContent = "Submitting...";
        window.clearInterval(interval);
    });
});
