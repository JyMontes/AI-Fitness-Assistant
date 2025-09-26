// JS para evitar múltiples llamadas a /next_exercise
let autoAdvance = true;
let advancing = false;

function advanceToNextExercise() {
    if (advancing) return;
    advancing = true;
    document.getElementById('nextBtn').disabled = true;
    window.location.href = '/next_exercise';
}

if (document.getElementById('nextBtn')) {
    document.getElementById('nextBtn').onclick = advanceToNextExercise;
}

setInterval(function() {
    if (advancing) return;
    fetch('/exercise_status')
        .then(response => response.json())
        .then(data => {
            if (data.finished) {
                document.getElementById('nextBtn').disabled = false;
                if (autoAdvance) {
                    advanceToNextExercise();
                }
            }
        });
}, 1000);
