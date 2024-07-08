// static/js/toggle_fields.js
document.addEventListener('DOMContentLoaded', function () {
    function toggleFormFields(switchElementId, fieldsContainerId) {
        var switchElement = document.getElementById(switchElementId);
        var formFields = document.getElementById(fieldsContainerId).querySelectorAll('.form-control');

        function toggleFields() {
            var isEnabled = switchElement.checked;
            formFields.forEach(function (field) {
                field.disabled = !isEnabled;
            });
        }

        switchElement.addEventListener('change', toggleFields);

        // Инициализация состояния полей формы при загрузке страницы
        toggleFields();
    }

    toggleFormFields('id_status_start_distance', 'start-distance-fields');
    toggleFormFields('id_status_number_cycles', 'number-cycles-fields');
    toggleFormFields('id_status_pace', 'pace-fields');
    toggleFormFields('id_status_underwater_part', 'underwater-part-fields');
});
