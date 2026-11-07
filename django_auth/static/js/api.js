// ===== Клиент REST API: все запросы страницы проходят через эту функцию =====
window.Api = (function () {

    class ApiError extends Error {
        constructor(message, status, fields) {
            super(message);
            this.status = status;      // HTTP-код ответа (0 — сервер недоступен)
            this.fields = fields || {}; // ошибки по полям формы
        }
    }

    function csrfToken() {
        const match = document.cookie.match(/csrftoken=([^;]+)/);
        return match ? match[1] : '';
    }

    // Понятное сообщение для пользователя вместо «Error 400» или «undefined»
    function describe(status, data) {
        const detail = data && data.detail;
        switch (status) {
            case 400: return 'Проверьте данные: некоторые поля заполнены неверно.';
            case 401:
            case 403: return detail || 'Операция запрещена: недостаточно прав.';
            case 404: return 'Запись не найдена — возможно, её уже удалил другой пользователь. Список обновлён.';
            case 409: return detail || 'Операцию нельзя выполнить из-за связанных данных.';
            default:
                return status >= 500
                    ? `Сервер вернул ошибку (${status}). Изменения не сохранены, попробуйте ещё раз позже.`
                    : `Не удалось выполнить запрос (код ${status}).`;
        }
    }

    // method: GET / POST / PUT / PATCH / DELETE; body — объект, который отправляется в JSON
    async function request(method, url, body) {
        const options = { method, headers: { 'Accept': 'application/json' } };
        if (method !== 'GET') options.headers['X-CSRFToken'] = csrfToken();
        if (body !== undefined) {
            options.headers['Content-Type'] = 'application/json';
            options.body = JSON.stringify(body);
        }

        let response;
        try {
            response = await fetch(url, options);
        } catch (e) {
            throw new ApiError('Нет связи с сервером. Проверьте, что сайт запущен, и повторите попытку.', 0);
        }

        if (response.status === 204) return null;               // DELETE — тела ответа нет
        const data = await response.json().catch(() => null);
        if (!response.ok) {
            const fields = response.status === 400 && data && !data.detail ? data : {};
            throw new ApiError(describe(response.status, data), response.status, fields);
        }
        return data;
    }

    return {
        get: url => request('GET', url),
        post: (url, body) => request('POST', url, body),
        put: (url, body) => request('PUT', url, body),
        patch: (url, body) => request('PATCH', url, body),
        remove: url => request('DELETE', url),
        ApiError,
    };
})();
