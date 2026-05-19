(function() {
    let interval = null;

    function startCountdown() {
        if (interval) clearInterval(interval);

        interval = setInterval(() => {
            const container = document.getElementById("timer-container");
            if (!container) { clearInterval(interval); return; }

            const running = container.dataset.running === "true";
            if (!running) { clearInterval(interval); return; }

            let remaining = parseInt(container.dataset.remaining, 10);
            if (remaining <= 0) {
                clearInterval(interval);
                htmx.ajax("POST", "/pomodoro/skip", {target: "#pomodoro-panel > div", swap: "innerHTML"});
                return;
            }

            remaining -= 1;
            container.dataset.remaining = remaining;
            const minutes = Math.floor(remaining / 60);
            const seconds = remaining % 60;
            const display = document.getElementById("countdown");
            if (display) {
                display.textContent = String(minutes).padStart(2, "0") + ":" + String(seconds).padStart(2, "0");
            }
        }, 1000);
    }

    document.addEventListener("htmx:afterSwap", function(event) {
        if (event.detail.target.closest("#pomodoro-panel")) {
            startCountdown();
        }
    });

    document.addEventListener("DOMContentLoaded", function() {
        startCountdown();
    });
})();
