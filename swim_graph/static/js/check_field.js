document.addEventListener('DOMContentLoaded', function() {
    // Инициализация Bootstrap Tooltips только при наведении
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl, {
            trigger: 'hover'  // Показывать только при наведении
        });
    });

    const timeInputs = document.querySelectorAll('[id^="timeInput_"]');

    timeInputs.forEach(input => {
        input.addEventListener('input', function () {
            const regex = /^\d{0,2}[.,]?\d{0,2}$/;
            if (!regex.test(input.value)) {
                input.value = input.value.slice(0, -1);
            }
        });
    });
});


