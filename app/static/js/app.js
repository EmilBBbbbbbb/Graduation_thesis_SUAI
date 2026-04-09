const chartContainer = document.getElementById('candlestick-chart');
const maButtonsContainer = document.getElementById('ma-buttons');
const maButtons = maButtonsContainer
    ? Array.from(maButtonsContainer.querySelectorAll('.ma-btn'))
    : [];

const resolveAutoMaPeriod = (visibleBars) => {
    if (visibleBars <= 40) return 10;
    if (visibleBars <= 120) return 20;
    if (visibleBars <= 260) return 50;
    return 100;
};

const calculateSma = (candles, period) => {
    if (!Number.isInteger(period) || period < 2 || candles.length < period) return [];

    const maData = [];
    let rollingSum = 0;

    for (let i = 0; i < candles.length; i += 1) {
        rollingSum += Number(candles[i].close) || 0;

        if (i >= period) {
            rollingSum -= Number(candles[i - period].close) || 0;
        }

        if (i >= period - 1) {
            maData.push({
                time: candles[i].time,
                value: Number((rollingSum / period).toFixed(2)),
            });
        }
    }

    return maData;
};

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

    const maSeries = chart.addLineSeries({
        color: '#60a5fa',
        lineWidth: 2,
        priceLineVisible: false,
        lastValueVisible: false,
    });

    const getSelectedMaValue = () => {
        const activeButton = maButtons.find((button) => button.classList.contains('is-active'));
        return activeButton ? activeButton.dataset.maValue : 'off';
    };

    const getVisibleBarsCount = () => {
        const logicalRange = chart.timeScale().getVisibleLogicalRange();
        if (!logicalRange) return seriesData.length;
        return Math.max(1, Math.round(logicalRange.to - logicalRange.from));
    };

    const updateMaSeries = () => {
        const selectedValue = getSelectedMaValue();

        if (selectedValue === 'off') {
            maSeries.setData([]);
            return;
        }

        let period;

        if (selectedValue === 'auto') {
            period = resolveAutoMaPeriod(getVisibleBarsCount());
        } else {
            period = Number.parseInt(selectedValue, 10);
        }

        maSeries.setData(calculateSma(seriesData, period));
    };

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

    maButtons.forEach((button) => {
        button.addEventListener('click', () => {
            maButtons.forEach((item) => item.classList.remove('is-active'));
            button.classList.add('is-active');
            updateMaSeries();
        });
    });

    chart.timeScale().subscribeVisibleLogicalRangeChange(() => {
        if (getSelectedMaValue() === 'auto') {
            updateMaSeries();
        }
    });

    updateMaSeries();

    chart.timeScale().fitContent();

    const volumeChartContainer = document.getElementById('volume-chart');
    if (volumeChartContainer) {
        const volumeChart = LightweightCharts.createChart(volumeChartContainer, {
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
            height: volumeChartContainer.clientHeight,
            width: volumeChartContainer.clientWidth,
        });

        const volumeSeries = volumeChart.addHistogramSeries({
            color: '#3b82f6',
        });

        const volumeData = seriesData.map(candle => ({
            time: candle.time,
            value: candle.volume || 0,
        }));

        volumeSeries.setData(volumeData);
        volumeChart.timeScale().fitContent();

        window.addEventListener('resize', () => {
            volumeChart.applyOptions({
                width: volumeChartContainer.clientWidth,
                height: volumeChartContainer.clientHeight,
            });
        });
    }

    const rsiChartContainer = document.getElementById('rsi-chart');
    if (rsiChartContainer) {
        const rsiChart = LightweightCharts.createChart(rsiChartContainer, {
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
                scaleMargins: {
                    top: 0.1,
                    bottom: 0.1,
                },
            },
            height: rsiChartContainer.clientHeight,
            width: rsiChartContainer.clientWidth,
        });

        const rsiLineSeries = rsiChart.addLineSeries({
            color: '#f59e0b',
            lineWidth: 2,
        });

        const rsiData = seriesData
            .filter(candle => 'rsi' in candle)
            .map(candle => ({
                time: candle.time,
                value: candle.rsi,
            }));

        if (rsiData.length > 0) {
            rsiLineSeries.setData(rsiData);
        }

        rsiChart.addLineSeries({
            color: 'rgba(239, 68, 68, 0.3)',
            lineWidth: 1,
        }).setData(seriesData.map(candle => ({
            time: candle.time,
            value: 70,
        })));

        rsiChart.addLineSeries({
            color: 'rgba(34, 197, 94, 0.3)',
            lineWidth: 1,
        }).setData(seriesData.map(candle => ({
            time: candle.time,
            value: 30,
        })));

        rsiChart.timeScale().fitContent();

        window.addEventListener('resize', () => {
            rsiChart.applyOptions({
                width: rsiChartContainer.clientWidth,
                height: rsiChartContainer.clientHeight,
            });
        });
    }

    window.addEventListener('resize', () => {
        chart.applyOptions({
            width: chartContainer.clientWidth,
            height: chartContainer.clientHeight,
        });
    });
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

