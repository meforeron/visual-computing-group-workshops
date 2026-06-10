document.addEventListener('DOMContentLoaded', () => {
    const fileInput    = document.getElementById('file-input');
    const cameraInput  = document.getElementById('camera-input');
    const cameraBtn    = document.getElementById('camera-btn');
    const dropZone     = document.getElementById('drop-zone');
    const loader       = document.getElementById('loader');
    const statusMsg    = document.getElementById('status-msg');
    const errorMsg     = document.getElementById('error-msg');
    const resultsContainer = document.getElementById('results-container');

    const elements = {
        original:  document.getElementById('img-original'),
        edge:      document.getElementById('img-edge'),
        scan:      document.getElementById('img-scan'),
        detection: document.getElementById('img-detection'),
        merchant:  document.getElementById('val-merchant'),
        date:      document.getElementById('val-date'),
        currency:  document.getElementById('val-currency'),
        tax:       document.getElementById('val-tax'),
        total:     document.getElementById('val-total'),
        raw:       document.getElementById('text-raw'),
        confBadge: document.getElementById('conf-badge'),
        statBlocks: document.getElementById('stat-blocks'),
        statConf:   document.getElementById('stat-conf'),
    };

    const exportBtn = document.getElementById('export-csv');
    let lastInfo = null;

    // --- File input (drop-zone click) ---
    dropZone.addEventListener('click', (e) => {
        if (e.target !== fileInput) fileInput.click();
    });
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) uploadFile(e.target.files[0]);
    });

    // --- Camera button (2.5) ---
    cameraBtn.addEventListener('click', () => cameraInput.click());
    cameraInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) uploadFile(e.target.files[0]);
    });

    // --- Drag & Drop ---
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.style.borderColor = 'var(--primary)';
    });
    dropZone.addEventListener('dragleave', () => {
        dropZone.style.borderColor = '';
    });
    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.style.borderColor = '';
        if (e.dataTransfer.files.length > 0) uploadFile(e.dataTransfer.files[0]);
    });

    // --- CSV export (2.6) ---
    function csvEscape(v) {
        const s = (v ?? '').toString();
        return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
    }
    exportBtn.addEventListener('click', () => {
        if (!lastInfo) return;
        const cols = ['Comercio', 'Fecha', 'Moneda', 'Impuestos', 'Total'];
        const header = cols.join(',');
        const row = cols.map((c) => csvEscape(lastInfo[c] || '')).join(',');
        const blob = new Blob(['﻿' + header + '\n' + row + '\n'], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `factura_${Date.now()}.csv`;
        a.click();
        URL.revokeObjectURL(url);
    });

    // --- Helpers ---
    function showError(msg) {
        errorMsg.textContent = msg;
        errorMsg.style.display = 'block';
    }
    function clearError() {
        errorMsg.textContent = '';
        errorMsg.style.display = 'none';
    }
    function setLoading(active) {
        loader.style.display    = active ? 'block' : 'none';
        statusMsg.style.display = active ? 'block' : 'none';
    }

    // --- Upload ---
    function uploadFile(file) {
        clearError();
        resultsContainer.classList.remove('visible');
        elements.confBadge.style.display = 'none';
        elements.statBlocks.innerHTML = '';
        elements.statConf.innerHTML = '';
        setLoading(true);

        const formData = new FormData();
        formData.append('file', file);

        fetch('/upload', { method: 'POST', body: formData })
            .then(async (response) => {
                const data = await response.json();
                setLoading(false);

                if (!response.ok || data.error) {
                    showError(data.error || 'Error desconocido en el procesamiento.');
                    return;
                }
                if (!data.images || !data.parsed_info) {
                    showError('Respuesta inesperada del servidor.');
                    return;
                }

                elements.original.src  = data.images.original;
                elements.edge.src      = data.images.edge;
                elements.scan.src      = data.images.scan;
                elements.detection.src = data.images.detection;

                const info = data.parsed_info;
                lastInfo = info;
                elements.merchant.textContent = info.Comercio  || '---';
                elements.date.textContent     = info.Fecha     || '---';
                elements.currency.textContent = info.Moneda    || '---';
                elements.tax.textContent      = info.Impuestos || '---';
                elements.total.textContent    = info.Total     || '---';
                elements.raw.textContent      = data.text;

                const conf = data.ocr_confidence ?? null;
                const blocks = data.ocr_blocks ?? null;
                if (conf !== null) {
                    const badge = elements.confBadge;
                    badge.textContent = `OCR ${conf}%`;
                    badge.className = 'conf-badge ' + (conf >= 75 ? 'conf-high' : conf >= 50 ? 'conf-mid' : 'conf-low');
                    badge.style.display = 'inline-block';
                    elements.statConf.innerHTML = `<i class="fas fa-chart-bar"></i> Confianza: <strong>${conf}%</strong>`;
                }
                if (blocks !== null) {
                    elements.statBlocks.innerHTML = `<i class="fas fa-th-large"></i> Bloques OCR: <strong>${blocks}</strong>`;
                }

                resultsContainer.classList.add('visible');
            })
            .catch(() => {
                setLoading(false);
                showError('Error de conexión. Verifica que el servidor esté activo.');
            });
    }
});
