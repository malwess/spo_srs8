// ===== «Мои обращения»: интерфейс работает только через REST API =====
(function () {
    const $ = id => document.getElementById(id);
    const modal = id => tabler.bootstrap.Modal.getOrCreateInstance($(id));
    const STATUS_COLORS = { new: 'blue', progress: 'orange', done: 'green' };
    const FIELD_NAMES = { title: 'Тема', category: 'Категория', course: 'Курс', status: 'Статус',
                          description: 'Описание', non_field_errors: 'Ошибка' };

    // ---------- Сообщения пользователю (без технического JSON) ----------
    function showMessage(text, isError = false) {
        const box = $('message');
        box.replaceChildren();
        const alert = document.createElement('div');
        alert.className = 'alert alert-dismissible ' + (isError ? 'alert-danger' : 'alert-success');
        const body = document.createElement('div');
        body.className = 'd-flex';
        const icon = document.createElement('i');
        icon.className = 'ti alert-icon ' + (isError ? 'ti-alert-circle' : 'ti-circle-check');
        const textEl = document.createElement('div');
        textEl.textContent = text;
        const close = document.createElement('a');
        close.className = 'btn-close';
        close.setAttribute('data-bs-dismiss', 'alert');
        body.append(icon, textEl);
        alert.append(body, close);
        box.append(alert);
    }

    // Ошибки по полям превращаются в читаемый текст: «Статус: Недопустимый переход…»
    function errorText(error) {
        const fields = Object.entries(error.fields || {});
        if (!fields.length) return error.message;
        return fields.map(([name, msgs]) => (FIELD_NAMES[name] || name) + ': ' + [].concat(msgs).join(' ')).join(' ');
    }

    function markFields(form, error) {
        form.querySelectorAll('.is-invalid').forEach(el => el.classList.remove('is-invalid'));
        form.querySelectorAll('[data-error]').forEach(el => { el.textContent = ''; });
        Object.entries(error.fields || {}).forEach(([name, msgs]) => {
            const field = form.elements[name];
            const box = form.querySelector('[data-error="' + name + '"]');
            if (field) field.classList.add('is-invalid');
            if (box) box.textContent = [].concat(msgs).join(' ');
        });
    }

    // ---------- Справочники из БД ----------
    async function loadSelect(select, url, label, emptyText) {
        const items = await Api.get(url);
        select.replaceChildren(new Option(emptyText, ''));
        items.forEach(item => select.append(new Option(item[label], item.id)));
    }

    // ---------- Список обращений ----------
    const list = $('tickets-list');
    const filter = $('status-filter');

    function badge(text, color) {
        const el = document.createElement('span');
        el.className = 'badge bg-' + color + '-lt';
        el.textContent = text;
        return el;
    }

    function button(cls, icon, title, onClick) {
        const b = document.createElement('button');
        b.type = 'button';
        b.className = 'btn btn-sm ' + cls;
        b.title = title;
        b.innerHTML = '<i class="ti ' + icon + '"></i>';
        b.addEventListener('click', onClick);
        return b;
    }

    function renderTicket(t) {
        const row = document.createElement('div');
        row.className = 'list-group-item';
        row.dataset.id = t.id;

        const top = document.createElement('div');
        top.className = 'd-flex flex-wrap align-items-start gap-2';

        const info = document.createElement('div');
        info.className = 'flex-fill';
        const title = document.createElement('div');
        title.className = 'fw-medium';
        title.textContent = t.title;                       // textContent — без интерпретации HTML
        const meta = document.createElement('div');
        meta.className = 'small text-secondary d-flex flex-wrap gap-2 mt-1';
        meta.append(badge(t.category_name, 'azure'));
        if (t.course_title) meta.append(badge(t.course_title, 'purple'));
        const date = document.createElement('span');
        date.textContent = '№ ' + t.id + ' · ' + new Date(t.created_at).toLocaleString('ru-RU');
        meta.append(date);
        info.append(title, meta);
        if (t.description) {
            const d = document.createElement('div');
            d.className = 'small mt-1';
            d.textContent = t.description;
            info.append(d);
        }

        // Смена статуса: в списке только допустимые переходы, которые прислал сервер
        const controls = document.createElement('div');
        controls.className = 'd-flex align-items-center gap-2';
        controls.append(badge(t.status_display, STATUS_COLORS[t.status]));
        if (t.next_statuses.length) {
            const select = document.createElement('select');
            select.className = 'form-select form-select-sm';
            select.style.width = 'auto';
            select.setAttribute('aria-label', 'Изменить статус');
            select.append(new Option('Изменить статус…', ''));
            t.next_statuses.forEach(s => select.append(new Option('→ ' + s.label, s.value)));
            select.addEventListener('change', () => select.value && changeStatus(t, select.value));
            controls.append(select);
            controls.append(button('btn-icon', 'ti-pencil', 'Изменить тему и описание', () => openEdit(t)));
        }
        controls.append(button('btn-icon btn-outline-danger', 'ti-trash', 'Удалить', () => askDelete(t)));

        top.append(info, controls);
        row.append(top);
        return row;
    }

    async function loadTickets() {
        $('loading').hidden = false;
        const params = new URLSearchParams();
        if (filter.value) params.set('status', filter.value);
        const url = '/api/tickets/' + (params.toString() ? '?' + params : '');
        $('request-url').textContent = 'GET ' + url;
        try {
            const tickets = await Api.get(url);
            $('count').textContent = tickets.length;
            list.replaceChildren();
            if (!tickets.length) {
                const empty = document.createElement('div');
                empty.className = 'list-group-item text-center text-secondary py-4';
                empty.textContent = 'Обращения не найдены';
                list.append(empty);
            }
            tickets.forEach(t => list.append(renderTicket(t)));
            return true;
        } catch (error) {
            showMessage('Не удалось загрузить обращения. ' + errorText(error), true);
            return false;
        } finally {
            $('loading').hidden = true;
        }
    }

    filter.addEventListener('change', loadTickets);
    $('reload').addEventListener('click', async () => {
        if (await loadTickets()) showMessage('Список заново получен из базы данных');
    });

    // ---------- POST: создание ----------
    const form = $('ticket-form');
    form.addEventListener('submit', async event => {
        event.preventDefault();
        markFields(form, {});
        try {
            const ticket = await Api.post('/api/tickets/', {
                title: form.elements.title.value,
                category: form.elements.category.value || null,
                course: form.elements.course.value || null,
                description: form.elements.description.value,
            });
            form.reset();
            showMessage(`Обращение «${ticket.title}» создано (№ ${ticket.id}, статус «${ticket.status_display}»)`);
            await loadTickets();
        } catch (error) {
            markFields(form, error);
            showMessage('Не удалось создать обращение. ' + errorText(error), true);
        }
    });

    // ---------- PATCH: смена статуса ----------
    async function changeStatus(ticket, status) {
        try {
            const saved = await Api.patch(`/api/tickets/${ticket.id}/`, { status });
            showMessage(`Статус обращения «${saved.title}» изменён: «${ticket.status_display}» → «${saved.status_display}»`);
        } catch (error) {
            showMessage('Статус не изменён. ' + errorText(error), true);
        }
        await loadTickets();
    }

    // ---------- PATCH: тема и описание ----------
    const editForm = $('edit-form');

    function openEdit(ticket) {
        markFields(editForm, {});
        editForm.querySelector('.form-errors').replaceChildren();
        editForm.dataset.id = ticket.id;
        editForm.elements.title.value = ticket.title;
        editForm.elements.description.value = ticket.description;
        modal('edit-modal').show();
    }

    editForm.addEventListener('submit', async event => {
        event.preventDefault();
        try {
            const saved = await Api.patch(`/api/tickets/${editForm.dataset.id}/`, {
                title: editForm.elements.title.value,
                description: editForm.elements.description.value,
            });
            modal('edit-modal').hide();
            showMessage(`Обращение «${saved.title}» сохранено`);
            await loadTickets();
        } catch (error) {
            markFields(editForm, error);
            const box = editForm.querySelector('.form-errors');
            box.replaceChildren();
            const alert = document.createElement('div');
            alert.className = 'alert alert-danger';
            alert.textContent = errorText(error);
            box.append(alert);
        }
    });

    // ---------- DELETE с подтверждением ----------
    let toDelete = null;

    function askDelete(ticket) {
        toDelete = ticket;
        $('confirm-text').textContent = `Вы действительно хотите удалить обращение «${ticket.title}»?`;
        modal('confirm-modal').show();
    }

    $('confirm-cancel').addEventListener('click', () => {
        if (toDelete) showMessage(`Удаление отменено: обращение «${toDelete.title}» осталось в списке`);
        toDelete = null;
    });

    $('confirm-ok').addEventListener('click', async () => {
        const ticket = toDelete;
        toDelete = null;
        modal('confirm-modal').hide();
        try {
            await Api.remove(`/api/tickets/${ticket.id}/`);
            showMessage(`Обращение «${ticket.title}» удалено`);
        } catch (error) {
            showMessage('Не удалось удалить обращение. ' + errorText(error), true);
        }
        await loadTickets();
    });

    // ---------- Запуск ----------
    (async function initialize() {
        try {
            await loadSelect(form.elements.category, '/api/categories/', 'name', 'Выберите категорию');
            await loadSelect(form.elements.course, '/api/courses/', 'title', 'Не относится к курсу');
            await loadTickets();
        } catch (error) {
            showMessage('Ошибка загрузки страницы. ' + errorText(error), true);
        }
    })();
})();
