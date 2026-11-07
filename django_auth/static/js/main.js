// ===== Скрипты проекта поверх Tabler =====
document.addEventListener("DOMContentLoaded", function () {

    // 1. Всплывающие подсказки (Tooltip из Bootstrap, входит в Tabler)
    document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(function (el) {
        new tabler.bootstrap.Tooltip(el);
    });

    // 2. Поиск по таблице без перезагрузки страницы
    document.querySelectorAll("[data-table-search]").forEach(function (input) {
        const table = document.querySelector(input.dataset.tableSearch);
        if (!table) return;
        const rows = Array.from(table.querySelectorAll("tbody tr"));
        const cols = table.querySelectorAll("thead th").length;

        const empty = document.createElement("tr");
        empty.className = "search-empty d-none";
        empty.innerHTML = '<td colspan="' + cols + '">Ничего не найдено</td>';
        table.querySelector("tbody").appendChild(empty);

        input.addEventListener("input", function () {
            const query = input.value.trim().toLowerCase();
            let shown = 0;
            rows.forEach(function (row) {
                const match = row.textContent.toLowerCase().includes(query);
                row.classList.toggle("d-none", !match);
                if (match) shown++;
            });
            empty.classList.toggle("d-none", shown > 0);
        });
    });

    // 3. Показать / скрыть пароль на странице входа
    const toggle = document.getElementById("toggle-password");
    if (toggle) {
        toggle.addEventListener("click", function (event) {
            event.preventDefault();
            const input = document.getElementById("id_password");
            const hidden = input.type === "password";
            input.type = hidden ? "text" : "password";
            toggle.querySelector("i").className = hidden ? "ti ti-eye-off" : "ti ti-eye";
        });
    }
});
