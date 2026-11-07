// ===== Запись на пересдачу: весь интерфейс работает через REST API =====
(function () {
    const root = document.getElementById('retakes');
    const $ = id => document.getElementById(id);
    const canManage = root.dataset.canManage === '1';
    const modal = id => tabler.bootstrap.Modal.getOrCreateInstance($(id));
    const COLORS = { draft: 'secondary', submitted: 'blue', approved: 'green', rejected: 'red', cancelled: 'orange' };
    const BTN = { submit: 'btn-primary', approve: 'btn-success', reject: 'btn-outline-danger', cancel: 'btn-outline-warning' };
    const FIELD = { slot: 'Время пересдачи', reason: 'Причина', status: 'Статус', comment: 'Комментарий' };
    let current = null;            // выбранная заявка

    const el = (tag, cls, text) => {
        const e = document.createElement(tag);
        if (cls) e.className = cls;
        if (text !== undefined) e.textContent = text;   // только textContent — без вставки HTML из данных
        return e;
    };
    const dt = v => new Date(v).toLocaleString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' });

    // ---------- сообщения ----------
    function errorText(error) {
        const fields = Object.entries(error.fields || {});
        if (!fields.length) return error.message;
        return fields.map(([k, v]) => (FIELD[k] ? FIELD[k] + ': ' : '') + [].concat(v).join(' ')).join(' ');
    }

    function show(text, isError = false) {
        const box = $('message');
        box.replaceChildren();
        const a = el('div', 'alert alert-dismissible ' + (isError ? 'alert-danger' : 'alert-success'));
        const row = el('div', 'd-flex');
        row.append(el('i', 'ti alert-icon ' + (isError ? 'ti-alert-circle' : 'ti-circle-check')), el('div', '', text));
        const close = el('a', 'btn-close');
        close.dataset.bsDismiss = 'alert';
        a.append(row, close);
        box.append(a);
    }

    // ---------- справочники ----------
    let slots = [];
    async function loadSlots() {
        slots = await Api.get('/api/retake-slots/?upcoming=1');
        const list = $('slots');
        list.replaceChildren();
        slots.forEach(s => {
            const item = el('div', 'list-group-item');
            const top = el('div', 'd-flex justify-content-between');
            top.append(el('div', 'fw-medium', s.course_title), el('span', 'badge bg-' + (s.free ? 'green' : 'red') + '-lt',
                s.free ? `свободно ${s.free} из ${s.capacity}` : 'мест нет'));
            const bar = el('div', 'progress progress-sm mt-2');
            const fill = el('div', 'progress-bar bg-' + (s.free ? 'blue' : 'red'));
            fill.style.width = Math.round(s.booked * 100 / s.capacity) + '%';
            bar.append(fill);
            item.append(top, el('div', 'small text-secondary', dt(s.starts_at) + ' · ауд. ' + s.room), bar);
            list.append(item);
        });
    }

    async function loadCourses() {
        const courses = await Api.get('/api/courses/');
        [$('filter-course'), $('f-course')].filter(Boolean).forEach(select => {
            courses.forEach(c => select.append(new Option(c.title, c.id)));
        });
        if ($('f-course')) $('f-course').options[0].textContent = 'Выберите курс';
    }

    function fillSlotSelect(courseId, selected) {
        const select = $('f-slot');
        select.replaceChildren(new Option(courseId ? 'Выберите время' : 'Сначала выберите курс', ''));
        slots.filter(s => String(s.course) === String(courseId)).forEach(s => {
            const o = new Option(`${dt(s.starts_at)}, ауд. ${s.room} — свободно ${s.free} из ${s.capacity}`, s.id);
            select.append(o);
        });
        if (selected) select.value = selected;
    }

    // ---------- список заявок (серверные фильтры) ----------
    async function loadRequests() {
        const params = new URLSearchParams();
        if ($('filter-status').value) params.set('status', $('filter-status').value);
        if ($('filter-course').value) params.set('course', $('filter-course').value);
        const url = '/api/retakes/' + (params.toString() ? '?' + params : '');
        $('request-url').textContent = 'GET ' + url;
        try {
            const items = await Api.get(url);
            $('count').textContent = items.length;
            const body = $('requests');
            body.replaceChildren();
            if (!items.length) {
                const tr = el('tr'); const td = el('td', 'text-center text-secondary py-4', 'Заявок не найдено');
                td.colSpan = 5; tr.append(td); body.append(tr);
            }
            items.forEach(r => {
                const tr = el('tr');
                tr.style.cursor = 'pointer';
                tr.classList.toggle('table-active', current && current.id === r.id);
                tr.append(el('td', 'text-secondary', '№ ' + r.id));
                if (canManage) tr.append(el('td', '', r.owner_name));
                const c = el('td');
                c.append(el('div', 'fw-medium', r.slot_info.course_title), el('div', 'small text-secondary', dt(r.slot_info.starts_at)));
                const st = el('td'); st.append(el('span', 'badge bg-' + COLORS[r.status] + '-lt', r.status_display));
                const go = el('td', 'text-end'); go.append(el('i', 'ti ti-chevron-right text-secondary'));
                tr.append(c, st, go);
                tr.addEventListener('click', () => openDetail(r.id));
                body.append(tr);
            });
            return true;
        } catch (error) {
            show('Не удалось загрузить заявки. ' + errorText(error), true);
            return false;
        }
    }

    // ---------- карточка и история ----------
    async function openDetail(id) {
        try {
            const [r, history] = await Promise.all([Api.get(`/api/retakes/${id}/`), Api.get(`/api/retakes/${id}/history/`)]);
            current = r;
            $('detail').hidden = false;
            $('detail-title').textContent = `Заявка № ${r.id} — ${r.status_display}`;
            const info = $('detail-info');
            info.replaceChildren();
            [['Студент', r.owner_name], ['Курс', r.slot_info.course_title],
             ['Пересдача', dt(r.slot_info.starts_at) + ', ауд. ' + r.slot_info.room],
             ['Занято мест', `${r.slot_info.booked} из ${r.slot_info.capacity}`],
             ['Причина', r.reason], ['Комментарий методиста', r.comment || '—']].forEach(([k, v]) => {
                info.append(el('div', 'small text-secondary', k), el('div', 'mb-2', v));
            });

            const actions = $('detail-actions');
            actions.replaceChildren();
            r.actions.forEach(a => {
                const b = el('button', 'btn btn-sm ' + BTN[a.name], a.label);
                b.addEventListener('click', () => askAction(r, a));
                actions.append(b);
            });
            if (!canManage && r.status === 'draft') {
                const e = el('button', 'btn btn-sm', 'Изменить');
                e.addEventListener('click', () => editDraft(r));
                actions.append(e);
            }
            if (!canManage && ['draft', 'cancelled'].includes(r.status)) {
                const d = el('button', 'btn btn-sm btn-icon btn-outline-danger');
                d.title = 'Удалить'; d.append(el('i', 'ti ti-trash'));
                d.addEventListener('click', () => askDelete(r));
                actions.append(d);
            }

            const list = $('history');
            list.replaceChildren();
            history.forEach(h => {
                const li = el('li', 'timeline-event');
                const icon = el('div', 'timeline-event-icon bg-' + (COLORS[h.new_status] || 'secondary') + '-lt');
                icon.append(el('i', 'ti ti-point'));
                const card = el('div', 'card timeline-event-card');
                const body = el('div', 'card-body py-2');
                const head = el('div', 'd-flex justify-content-between gap-2');
                head.append(el('div', 'fw-medium', h.action_display), el('div', 'small text-secondary text-nowrap', dt(h.created_at)));
                body.append(head, el('div', 'small text-secondary', 'Инициатор: ' + h.actor_name));
                if (h.details) body.append(el('div', 'small', h.details));
                card.append(body);
                li.append(icon, card);
                list.append(li);
            });
            document.querySelectorAll('#requests tr').forEach(tr => tr.classList.remove('table-active'));
        } catch (error) {
            show('Не удалось открыть заявку. ' + errorText(error), true);
            if (error.status === 404) { $('detail').hidden = true; current = null; loadRequests(); }
        }
    }

    async function refresh(id) {
        await Promise.all([loadRequests(), loadSlots()]);
        if (id) await openDetail(id);
    }

    // ---------- действия бизнес-процесса (POST /api/retakes/<id>/<action>/) ----------
    let pending = null;
    function confirmBox(title, text, okLabel, danger, needComment, action) {
        $('confirm-title').textContent = title;
        $('confirm-text').textContent = text;
        $('confirm-ok').textContent = okLabel;
        $('confirm-ok').className = 'btn w-100 ' + (danger ? 'btn-danger' : 'btn-primary');
        $('confirm-status').className = 'modal-status ' + (danger ? 'bg-danger' : 'bg-primary');
        $('confirm-comment').hidden = !needComment;
        $('confirm-comment').value = '';
        pending = action;
        modal('confirm-modal').show();
    }

    function askAction(r, a) {
        const texts = {
            submit: `Подать заявку № ${r.id}? Для неё будет забронировано место на пересдаче.`,
            approve: `Одобрить заявку № ${r.id} студента ${r.owner_name}?`,
            reject: `Отклонить заявку № ${r.id}? Место на пересдаче освободится.`,
            cancel: `Отменить заявку № ${r.id}?` + (r.status === 'submitted' ? ' Место на пересдаче освободится.' : ''),
        };
        confirmBox(a.label + ' заявку', texts[a.name], a.label, ['reject', 'cancel'].includes(a.name), a.name === 'reject',
            async comment => {
                const saved = await Api.post(`/api/retakes/${r.id}/${a.name}/`, { comment });
                show(`Заявка № ${saved.id}: статус «${saved.status_display}».`);
                await refresh(saved.id);
            });
    }

    function askDelete(r) {
        confirmBox('Удаление заявки', `Вы действительно хотите удалить заявку № ${r.id} по курсу «${r.slot_info.course_title}»?`,
            'Удалить', true, false, async () => {
                await Api.remove(`/api/retakes/${r.id}/`);
                show(`Заявка № ${r.id} удалена.`);
                $('detail').hidden = true; current = null;
                await refresh();
            });
    }

    $('confirm-cancel').addEventListener('click', () => { if (pending) show('Действие отменено — заявка не изменилась.'); pending = null; });
    $('confirm-ok').addEventListener('click', async () => {
        const action = pending; pending = null;
        const comment = $('confirm-comment').value;
        modal('confirm-modal').hide();
        try {
            await action(comment);
        } catch (error) {
            show('Операция не выполнена. ' + errorText(error), true);
            if (current) refresh(current.id);
        }
    });

    // ---------- форма черновика: POST или PATCH ----------
    const form = $('request-form');
    if (form) {
        $('f-course').addEventListener('change', () => fillSlotSelect($('f-course').value));
        $('form-reset').addEventListener('click', resetForm);

        form.addEventListener('submit', async e => {
            e.preventDefault();
            form.querySelectorAll('.is-invalid').forEach(x => x.classList.remove('is-invalid'));
            form.querySelectorAll('[data-error]').forEach(x => { x.textContent = ''; });
            const data = { slot: $('f-slot').value || null, reason: $('f-reason').value };
            const id = form.dataset.id;
            try {
                const saved = id ? await Api.patch(`/api/retakes/${id}/`, data) : await Api.post('/api/retakes/', data);
                show(id ? `Черновик № ${saved.id} сохранён.` : `Черновик заявки № ${saved.id} создан. Чтобы забронировать место, нажмите «Подать».`);
                resetForm();
                await refresh(saved.id);
            } catch (error) {
                Object.entries(error.fields || {}).forEach(([k, v]) => {
                    const f = form.elements[k]; const b = form.querySelector(`[data-error="${k}"]`);
                    if (f) f.classList.add('is-invalid');
                    if (b) b.textContent = [].concat(v).join(' ');
                });
                show('Черновик не сохранён. ' + errorText(error), true);
            }
        });
    }

    function editDraft(r) {
        form.dataset.id = r.id;
        $('form-title').textContent = `Изменение черновика № ${r.id}`;
        $('form-reset').hidden = false;
        $('f-course').value = r.slot_info.course;
        fillSlotSelect(r.slot_info.course, r.slot);
        $('f-reason').value = r.reason;
    }

    function resetForm() {
        if (!form) return;
        form.reset();
        delete form.dataset.id;
        $('form-title').textContent = 'Новая заявка';
        $('form-reset').hidden = true;
        fillSlotSelect('');
    }

    ['filter-status', 'filter-course'].forEach(id => $(id).addEventListener('change', loadRequests));

    (async () => {
        try {
            await Promise.all([loadCourses(), loadSlots()]);
            await loadRequests();
        } catch (error) {
            show('Ошибка загрузки страницы. ' + errorText(error), true);
        }
    })();
})();
