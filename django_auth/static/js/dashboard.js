// ===== Дашборд: загрузка данных из API, фильтры, KPI, графики и таблицы =====
(function () {
    const root = document.getElementById('dashboard');
    const form = document.getElementById('dashboard-filters');
    const updated = document.getElementById('updated-at');

    // --- Фильтры хранятся в адресе страницы, поэтому ссылкой можно поделиться ---
    function readFilters() {
        const values = {};
        new FormData(form).forEach((value, key) => { if (value) values[key] = value; });
        return values;
    }

    function applyUrlFilters() {
        const params = new URLSearchParams(location.search);
        params.forEach((value, key) => { if (form.elements[key]) form.elements[key].value = value; });
    }

    // Список групп показывает только группы выбранного факультета
    function syncGroups() {
        const group = form.elements.group;
        const dep = form.elements.department ? form.elements.department.value : '';
        if (!group) return;
        group.querySelectorAll('option[data-department]').forEach(o => {
            o.hidden = dep !== '' && o.dataset.department !== dep;
        });
        if (group.selectedOptions[0] && group.selectedOptions[0].hidden) group.value = '';
    }

    // --- KPI: числа плавно «досчитываются» до нового значения ---
    function setKpi(el, value) {
        const suffix = el.dataset.suffix || '';
        const target = Number(value);
        const from = Number(el.dataset.value || 0);
        const decimals = Number.isInteger(target) ? 0 : 2;
        el.dataset.value = target;
        const start = performance.now();
        function step(now) {
            const k = Math.min(1, (now - start) / 500);
            el.textContent = (from + (target - from) * k).toFixed(decimals).replace('.', ',') + suffix;
            if (k < 1) requestAnimationFrame(step);
        }
        requestAnimationFrame(step);
    }

    // --- Таблица-компонент: колонки описаны в атрибуте data-columns ---
    function renderTable(table, rows) {
        const columns = table.dataset.columns.split(',').map(c => c.split(':'));
        table.querySelector('thead tr').innerHTML = columns.map(([, title]) => '<th>' + title + '</th>').join('');
        if (!rows.length) {
            table.querySelector('tbody').innerHTML = '<tr><td colspan="' + columns.length +
                '" class="text-secondary">Нет данных для выбранных фильтров</td></tr>';
            return;
        }
        table.querySelector('tbody').innerHTML = rows.map((row, i) => '<tr>' + columns.map(([key]) => {
            if (key === 'place') return '<td class="text-secondary">' + (i + 1) + '</td>';
            if (key === 'success') {
                return '<td style="min-width:140px"><div class="d-flex align-items-center gap-2"><span>' + row.success +
                    '%</span><div class="progress progress-sm flex-fill"><div class="progress-bar bg-teal" style="width:' +
                    row.success + '%"></div></div></div></td>';
            }
            if (key === 'avg') {
                const color = row.avg >= 4.5 ? 'green' : row.avg >= 3.5 ? 'blue' : 'orange';
                return '<td><span class="badge bg-' + color + '-lt">' + String(row.avg).replace('.', ',') + '</span></td>';
            }
            return '<td>' + row[key] + '</td>';
        }).join('') + '</tr>').join('');
    }

    // Нажатие на сектор «Студенты по факультетам» открывает дашборд выбранного факультета
    function drillDown(data, index) {
        if (data.ids) location.href = '/analytics/structure/?department=' + data.ids[index];
    }

    // --- Главная функция: запрос к API и обновление всех компонентов ---
    async function load() {
        const filters = readFilters();
        const query = new URLSearchParams(filters).toString();
        history.replaceState(null, '', location.pathname + (query ? '?' + query : ''));
        document.querySelectorAll('[data-keep-filters]').forEach(a => {
            a.search = query;
        });
        root.classList.add('loading');
        const response = await fetch(root.dataset.api + (query ? '?' + query : ''));
        const data = await response.json();

        Object.entries(data.kpi).forEach(([key, value]) => {
            root.querySelectorAll('[data-kpi="' + key + '"]').forEach(el => setKpi(el, value));
        });
        Object.entries(data.charts).forEach(([key, value]) => {
            const el = root.querySelector('[data-chart="' + key + '"]');
            if (el) Charts.render(el, value, key === 'students_by_department' ? drillDown : null);
        });
        Object.entries(data.tables || {}).forEach(([key, rows]) => {
            const table = root.querySelector('[data-table="' + key + '"]');
            if (table) renderTable(table, rows);
        });
        updated.textContent = 'данные из БД, обновлено в ' + data.generated_at;
        root.classList.remove('loading');
    }

    form.addEventListener('change', event => {
        if (event.target.name === 'department') syncGroups();
        load();
    });
    document.getElementById('refresh').addEventListener('click', load);
    document.getElementById('reset-filters').addEventListener('click', () => {
        form.reset();
        syncGroups();
        load();
    });

    applyUrlFilters();
    syncGroups();
    load();
})();
