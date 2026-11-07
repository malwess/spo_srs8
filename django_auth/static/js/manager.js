// ===== Менеджер данных: интерфейс работает только через REST API =====
(function () {
    const $ = id => document.getElementById(id);
    const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
    const modal = id => tabler.bootstrap.Modal.getOrCreateInstance($(id));

    let departments = [];          // список факультетов, полученный из GET /api/departments/

    // ---------- Сообщения пользователю ----------
    function toast(text, color = 'success') {
        const el = document.createElement('div');
        el.className = 'toast align-items-center border-0 text-bg-' + color;
        el.innerHTML = '<div class="d-flex"><div class="toast-body">' + esc(text) +
            '</div><button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button></div>';
        $('toasts').appendChild(el);
        el.addEventListener('hidden.bs.toast', () => el.remove());
        new tabler.bootstrap.Toast(el, { delay: 4000 }).show();
    }

    function showError(error, box = $('error-box')) {
        const icon = error.status === 403 ? 'ti-lock' : error.status === 0 || error.status >= 500 ? 'ti-server-off' : 'ti-alert-circle';
        const code = error.status ? ` <span class="badge bg-red-lt ms-1">код ${error.status}</span>` : '';
        box.innerHTML = '<div class="alert alert-danger alert-dismissible" role="alert"><div class="d-flex">' +
            '<i class="ti ' + icon + ' alert-icon"></i><div>' + esc(error.message) + code + '</div></div>' +
            '<a class="btn-close" data-bs-dismiss="alert" aria-label="Закрыть"></a></div>';
    }

    function clearErrors(form) {
        form.querySelector('.form-errors').innerHTML = '';
        form.querySelectorAll('.is-invalid').forEach(el => el.classList.remove('is-invalid'));
        form.querySelectorAll('[data-error]').forEach(el => { el.textContent = ''; });
    }

    // Ошибки валидации из ответа 400 выводятся под соответствующими полями
    function showFormErrors(form, error) {
        showError(error, form.querySelector('.form-errors'));
        Object.entries(error.fields).forEach(([name, messages]) => {
            const field = form.elements[name];
            const box = form.querySelector('[data-error="' + name + '"]');
            if (field) field.classList.add('is-invalid');
            if (box) box.textContent = [].concat(messages).join(' ');
        });
    }

    // ---------- Факультеты (связанная сущность) ----------
    async function loadDepartments() {
        departments = await Api.get('/api/departments/');
        $('departments-count').textContent = departments.length;
        // выпадающие списки фильтра и формы курса заполняются данными из API
        document.querySelectorAll('.js-departments').forEach(select => {
            const value = select.value;
            select.querySelectorAll('option[value]:not([value=""])').forEach(o => o.remove());
            departments.forEach(d => select.insertAdjacentHTML('beforeend',
                '<option value="' + d.id + '">' + esc(d.name) + '</option>'));
            select.value = departments.some(d => String(d.id) === value) ? value : '';
        });
        $('departments-body').innerHTML = departments.map(d => `
            <tr>
                <td>${esc(d.name)}</td>
                <td class="text-center">${d.courses_count}</td>
                <td class="text-center">${d.groups_count}</td>
                <td><div class="btn-list flex-nowrap">
                    <button class="btn btn-sm btn-icon" data-edit-department="${d.id}" title="Изменить"><i class="ti ti-pencil"></i></button>
                    <button class="btn btn-sm btn-icon btn-outline-danger" data-delete-department="${d.id}" title="Удалить"><i class="ti ti-trash"></i></button>
                </div></td>
            </tr>`).join('');
    }

    // ---------- Курсы: серверная фильтрация ----------
    const filters = $('course-filters');
    let timer = null;

    function coursesUrl() {
        const params = new URLSearchParams();
        ['search', 'department', 'ordering'].forEach(name => {
            const value = filters.elements[name].value.trim();
            if (value) params.set(name, value);
        });
        const query = params.toString();
        return '/api/courses/' + (query ? '?' + decodeURIComponent(query) : '');
    }

    async function loadCourses() {
        const url = coursesUrl();
        $('request-url').textContent = 'GET ' + url;
        try {
            const courses = await Api.get(url);
            $('courses-count').textContent = courses.length;
            $('courses-body').innerHTML = courses.length ? courses.map(c => `
                <tr data-id="${c.id}">
                    <td><div class="fw-medium">${esc(c.title)}</div>
                        <div class="small text-secondary text-truncate" style="max-width: 360px">${esc(c.description) || 'Нет описания'}</div></td>
                    <td><span class="badge bg-azure-lt">${esc(c.department_name)}</span></td>
                    <td class="text-center">${c.students_count}</td>
                    <td class="text-center">${c.grades_count}</td>
                    <td class="text-center">${c.avg_grade ? c.avg_grade.toFixed(2).replace('.', ',') : '—'}</td>
                    <td><div class="btn-list flex-nowrap">
                        <button class="btn btn-sm btn-icon" data-edit-course="${c.id}" title="Изменить"><i class="ti ti-pencil"></i></button>
                        <button class="btn btn-sm btn-icon btn-outline-danger" data-delete-course="${c.id}" data-title="${esc(c.title)}" title="Удалить"><i class="ti ti-trash"></i></button>
                    </div></td>
                </tr>`).join('')
                : '<tr><td colspan="6" class="text-center text-secondary py-4">По выбранным условиям курсов не найдено</td></tr>';
        } catch (error) {
            showError(error);
        }
    }

    filters.addEventListener('change', loadCourses);
    filters.addEventListener('submit', e => e.preventDefault());
    filters.elements.search.addEventListener('input', () => { clearTimeout(timer); timer = setTimeout(loadCourses, 300); });
    $('reset-filters').addEventListener('click', () => { filters.reset(); loadCourses(); });

    // ---------- Форма курса: POST (новый) или PATCH (изменение) ----------
    const courseForm = $('course-form');

    async function openCourse(id) {
        clearErrors(courseForm);
        courseForm.reset();
        courseForm.dataset.id = id || '';
        courseForm.querySelector('.modal-title').textContent = id ? 'Изменение курса' : 'Новый курс';
        if (id) {
            try {
                const course = await Api.get('/api/courses/' + id + '/');   // свежие данные с сервера
                courseForm.elements.title.value = course.title;
                courseForm.elements.department.value = course.department;
                courseForm.elements.description.value = course.description;
            } catch (error) {
                showError(error);
                if (error.status === 404) loadCourses();
                return;
            }
        }
        modal('course-modal').show();
    }

    courseForm.addEventListener('submit', async event => {
        event.preventDefault();
        clearErrors(courseForm);
        const data = {
            title: courseForm.elements.title.value,
            department: courseForm.elements.department.value || null,
            description: courseForm.elements.description.value,
        };
        const id = courseForm.dataset.id;
        try {
            const saved = id ? await Api.patch('/api/courses/' + id + '/', data)
                             : await Api.post('/api/courses/', data);
            modal('course-modal').hide();
            toast(id ? `Курс «${saved.title}» сохранён` : `Курс «${saved.title}» добавлен (id ${saved.id})`);
            $('error-box').innerHTML = '';
            await Promise.all([loadCourses(), loadDepartments()]);
        } catch (error) {
            if (error.status === 404) { modal('course-modal').hide(); showError(error); loadCourses(); }
            else showFormErrors(courseForm, error);
        }
    });

    // ---------- Форма факультета: POST или PUT ----------
    const depForm = $('department-form');

    function openDepartment(id) {
        clearErrors(depForm);
        depForm.reset();
        depForm.dataset.id = id || '';
        const dep = departments.find(d => String(d.id) === String(id));
        depForm.querySelector('.modal-title').textContent = id ? 'Изменение факультета' : 'Новый факультет';
        if (dep) depForm.elements.name.value = dep.name;
        modal('department-modal').show();
    }

    depForm.addEventListener('submit', async event => {
        event.preventDefault();
        clearErrors(depForm);
        const id = depForm.dataset.id;
        const data = { name: depForm.elements.name.value };
        try {
            const saved = id ? await Api.put('/api/departments/' + id + '/', data)
                             : await Api.post('/api/departments/', data);
            modal('department-modal').hide();
            toast(id ? `Факультет переименован: «${saved.name}»` : `Факультет «${saved.name}» добавлен`);
            await Promise.all([loadDepartments(), loadCourses()]);
        } catch (error) {
            if (error.status === 404) { modal('department-modal').hide(); showError(error); loadDepartments(); }
            else showFormErrors(depForm, error);
        }
    });

    // ---------- Удаление с подтверждением ----------
    let pendingDelete = null;

    function confirmDelete(text, action) {
        $('confirm-text').innerHTML = text;
        pendingDelete = action;
        modal('confirm-modal').show();
    }

    $('confirm-ok').addEventListener('click', async () => {
        modal('confirm-modal').hide();
        try {
            await pendingDelete();
        } catch (error) {
            showError(error);
            if (error.status === 404) { loadCourses(); loadDepartments(); }
        }
    });

    // ---------- Делегирование кликов по кнопкам в таблицах ----------
    document.addEventListener('click', event => {
        const t = event.target.closest('button');
        if (!t) return;
        if (t.id === 'add-course') openCourse(null);
        if (t.id === 'add-department') openDepartment(null);
        if (t.dataset.editCourse) openCourse(t.dataset.editCourse);
        if (t.dataset.editDepartment) openDepartment(t.dataset.editDepartment);
        if (t.dataset.deleteCourse) {
            const { deleteCourse: id, title } = t.dataset;
            confirmDelete(`Вы действительно хотите удалить курс <b>«${esc(title)}»</b>? Вместе с ним будут удалены его оценки.`,
                async () => {
                    await Api.remove('/api/courses/' + id + '/');
                    toast(`Курс «${title}» удалён`);
                    $('error-box').innerHTML = '';
                    await Promise.all([loadCourses(), loadDepartments()]);
                });
        }
        if (t.dataset.deleteDepartment) {
            const dep = departments.find(d => String(d.id) === t.dataset.deleteDepartment);
            confirmDelete(`Вы действительно хотите удалить факультет <b>«${esc(dep.name)}»</b>?`, async () => {
                await Api.remove('/api/departments/' + dep.id + '/');
                toast(`Факультет «${dep.name}» удалён`);
                $('error-box').innerHTML = '';
                await loadDepartments();
            });
        }
        if (t.dataset.tab) {
            document.querySelectorAll('#tabs [data-tab]').forEach(b => b.classList.toggle('active', b === t));
            document.querySelectorAll('[data-panel]').forEach(p => { p.hidden = p.dataset.panel !== t.dataset.tab; });
        }
    });

    // ---------- Первая загрузка ----------
    loadDepartments().then(loadCourses).catch(showError);
})();
