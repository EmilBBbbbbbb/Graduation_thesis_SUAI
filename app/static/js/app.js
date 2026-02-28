const chartContainer = document.getElementById('candlestick-chart');

if (chartContainer && window.LightweightCharts) {
    const rawData = chartContainer.dataset.series;
    const rawPredictData = chartContainer.dataset.predictSeries;

    const seriesData = rawData ? JSON.parse(rawData) : [];
    const predictData = rawPredictData ? JSON.parse(rawPredictData) : [];


    const chart = LightweightCharts.createChart(chartContainer, {
        layout: {
            background: { color: '#101621' },
            textColor: '#cbd5f5',
            fontFamily: 'Inter, sans-serif',
        },
        grid: {
            vertLines: { color: 'rgba(148, 163, 184, 0.1)' },
            horzLines: { color: 'rgba(148, 163, 184, 0.1)' },
        },
        timeScale: {
            borderColor: 'rgba(148, 163, 184, 0.2)',
        },
        rightPriceScale: {
            borderColor: 'rgba(148, 163, 184, 0.2)',
        },
        crosshair: {
            mode: LightweightCharts.CrosshairMode.Normal,
        },
        height: chartContainer.clientHeight,
        width: chartContainer.clientWidth,
    });

    const candlestickSeries = chart.addCandlestickSeries({
        upColor: '#22c55e',
        downColor: '#ef4444',
        borderUpColor: '#22c55e',
        borderDownColor: '#ef4444',
        wickUpColor: '#22c55e',
        wickDownColor: '#ef4444',
    });

    candlestickSeries.setData(seriesData);

    if (predictData.length > 0) {
        const predictCandlestickSeries = chart.addCandlestickSeries({
            upColor: '#40E0D0',
            downColor: '#a963ea',
            borderUpColor: '#40E0D0',
            borderDownColor: '#a963ea',
            wickUpColor: '#40E0D0',
            wickDownColor: '#a963ea',
            priceLineVisible: true,
            lastValueVisible: true,
        });
        predictCandlestickSeries.setData(predictData);
    }

    chart.timeScale().fitContent();

    const handleResize = () => {
        chart.applyOptions({
            width: chartContainer.clientWidth,
            height: chartContainer.clientHeight,
        });
    };

    window.addEventListener('resize', handleResize);
}

const modal = document.getElementById('news-modal');
const modalTitle = document.getElementById('modal-title');
const modalDate = document.getElementById('modal-date');
const modalBody = document.getElementById('modal-body');

const openModal = (card) => {
    if (!modal) return;
    modalTitle.textContent = card.dataset.title || '';
    modalDate.textContent = card.dataset.date || '';
    modalBody.textContent = card.dataset.body || '';
    modal.classList.add('is-open');
    modal.setAttribute('aria-hidden', 'false');
};

const closeModal = () => {
    if (!modal) return;
    modal.classList.remove('is-open');
    modal.setAttribute('aria-hidden', 'true');
};

document.querySelectorAll('.news-card').forEach((card) => {
    card.addEventListener('click', () => openModal(card));
});

document.querySelectorAll('[data-modal-close]').forEach((element) => {
    element.addEventListener('click', closeModal);
});

document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') {
        closeModal();
    }
});
