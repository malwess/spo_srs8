// ===== Компонент графика: одна функция строит любой график дашбордов =====
// Тип графика задаётся в шаблоне атрибутом data-type, данные приходят из API.
window.Charts = (function () {
    const COLORS = ['#066fd1', '#2fb344', '#f76707', '#ae3ec9', '#0ca678', '#d63939', '#f59f00', '#4263eb'];
    const GRADE_COLORS = ['#d63939', '#f59f00', '#066fd1', '#2fb344'];          // 2, 3, 4, 5
    const instances = {};

    // Общие настройки для всех графиков
    function base(type, height) {
        return {
            chart: {
                type, height, fontFamily: 'inherit', parentHeightOffset: 0,
                toolbar: { show: true, tools: { download: true, selection: false, zoom: false, zoomin: false,
                                                 zoomout: false, pan: false, reset: false } },
                animations: { enabled: true, speed: 400 },
            },
            colors: COLORS,
            dataLabels: { enabled: false },
            grid: { strokeDashArray: 4 },
            legend: { position: 'bottom' },
            noData: { text: 'Нет данных' },
            theme: { mode: document.documentElement.getAttribute('data-bs-theme') === 'dark' ? 'dark' : 'light' },
        };
    }

    // Настройки для каждого вида графика (пресеты компонента)
    const PRESETS = {
        bar: (d, h) => ({ ...base('bar', h), series: d.series, xaxis: { categories: d.labels },
            plotOptions: { bar: { borderRadius: 4, columnWidth: '50%' } } }),
        hbar: (d, h) => ({ ...base('bar', h), series: d.series, xaxis: { categories: d.labels },
            plotOptions: { bar: { horizontal: true, borderRadius: 4, barHeight: '55%' } }, dataLabels: { enabled: true } }),
        score: (d, h) => ({ ...base('bar', h), series: d.series, xaxis: { categories: d.labels },
            yaxis: { min: 2, max: 5, tickAmount: 3, labels: { formatter: v => v.toFixed(1) } }, dataLabels: { enabled: true },
            plotOptions: { bar: { borderRadius: 4, columnWidth: '45%', distributed: true } }, legend: { show: false } }),
        score_h: (d, h) => ({ ...base('bar', h), series: d.series, xaxis: { categories: d.labels, min: 2, max: 5 },
            dataLabels: { enabled: true }, plotOptions: { bar: { horizontal: true, borderRadius: 4, distributed: true } },
            legend: { show: false } }),
        stacked: (d, h) => ({ ...base('bar', h), series: d.series, xaxis: { categories: d.labels },
            colors: [...GRADE_COLORS].reverse(), chart: { ...base('bar', h).chart, stacked: true },
            plotOptions: { bar: { borderRadius: 2, columnWidth: '55%' } } }),
        grades: (d, h) => ({ ...base('bar', h), series: d.series, xaxis: { categories: d.labels.map(v => 'Оценка ' + v) },
            colors: GRADE_COLORS, dataLabels: { enabled: true },
            plotOptions: { bar: { distributed: true, borderRadius: 4, columnWidth: '55%' } }, legend: { show: false } }),
        donut: (d, h) => ({ ...base('donut', h), series: d.series, labels: d.labels,
            dataLabels: { enabled: true },
            plotOptions: { pie: { donut: { size: '60%', labels: { show: true, total: { show: true, label: 'Всего' } } } } } }),
        line: (d, h) => ({ ...base('line', h), xaxis: { categories: d.labels },
            series: d.series.map((s, i) => ({ ...s, type: i === 0 ? 'column' : 'line' })),
            stroke: { width: [0, 3], curve: 'smooth' }, markers: { size: [0, 4] },
            plotOptions: { bar: { columnWidth: '45%', borderRadius: 3 } } }),
        trend: (d, h) => ({ ...base('line', h), xaxis: { categories: d.labels },
            series: d.series.map((s, i) => ({ ...s, type: i === 0 ? 'line' : 'column' })),
            stroke: { width: [3, 0], curve: 'smooth' }, markers: { size: [4, 0] },
            yaxis: [{ min: 2, max: 5, tickAmount: 3, title: { text: 'Балл' }, labels: { formatter: v => v.toFixed(1) } },
                    { opposite: true, title: { text: 'Оценок' }, labels: { formatter: v => Math.round(v) } }],
            plotOptions: { bar: { columnWidth: '45%', borderRadius: 3 } }, colors: ['#066fd1', '#c8d9f1'] }),
    };

    function isEmpty(d) {
        if (!d || !d.labels || !d.labels.length) return true;
        const values = typeof d.series[0] === 'number' ? d.series : d.series.flatMap(s => s.data);
        return values.every(v => !v);
    }

    // Построить или обновить график внутри карточки
    function render(el, data, onClick) {
        const id = el.dataset.chart;
        const empty = el.parentElement.querySelector('.chart-empty');
        empty.hidden = !isEmpty(data);
        el.hidden = isEmpty(data);
        if (isEmpty(data)) return;

        const height = parseInt(el.style.minHeight, 10) || 280;
        const options = PRESETS[el.dataset.type](data, height);
        if (onClick) {
            options.chart.events = { dataPointSelection: (e, ctx, cfg) => onClick(data, cfg.dataPointIndex) };
        }
        if (instances[id]) {
            instances[id].updateOptions(options, true, true);   // перерисовка с анимацией
        } else {
            instances[id] = new ApexCharts(el, options);
            instances[id].render();
        }
    }

    return { render };
})();
