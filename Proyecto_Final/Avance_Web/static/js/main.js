document.addEventListener('DOMContentLoaded', () => {
    const fileInput    = document.getElementById('file-input');
    const cameraInput  = document.getElementById('camera-input');
    const cameraBtn    = document.getElementById('camera-btn');
    const dropZone     = document.getElementById('drop-zone');
    const loader       = document.getElementById('loader');
    const statusMsg    = document.getElementById('status-msg');
    const errorMsg     = document.getElementById('error-msg');
    const resultsContainer = document.getElementById('results-container');
    const previewStrip = document.getElementById('preview-strip');
    const previewThumb = document.getElementById('preview-thumb');
    const previewName  = document.getElementById('preview-name');
    const previewSize  = document.getElementById('preview-size');
    const pipelineSteps = document.getElementById('pipeline-steps');
    const toastContainer = document.getElementById('toast-container');

    const elements = {
        original:   document.getElementById('img-original'),
        edge:       document.getElementById('img-edge'),
        scan:       document.getElementById('img-scan'),
        detection:  document.getElementById('img-detection'),
        merchant:   document.getElementById('val-merchant'),
        date:       document.getElementById('val-date'),
        currency:   document.getElementById('val-currency'),
        tax:        document.getElementById('val-tax'),
        total:      document.getElementById('val-total'),
        raw:        document.getElementById('text-raw'),
        confBadge:  document.getElementById('conf-badge'),
        statBlocks: document.getElementById('stat-blocks'),
        statConf:   document.getElementById('stat-conf'),
    };

    const exportBtn = document.getElementById('export-csv');
    let lastInfo = null;

    /* ── Toast helper ────────────────────────────────────── */
    function showToast(title, msg, type = 'success') {
        if (!toastContainer) return;
        const icon = type === 'success' ? 'fa-check-circle' : 'fa-exclamation-circle';
        const el = document.createElement('div');
        el.className = `toast toast-${type}`;
        el.innerHTML = `
            <i class="fas ${icon} toast-icon"></i>
            <div class="toast-body">
                <div class="toast-title">${title}</div>
                <div class="toast-msg">${msg}</div>
            </div>`;
        toastContainer.appendChild(el);
        setTimeout(() => {
            el.style.animation = 'toastOut 0.4s ease forwards';
            setTimeout(() => el.remove(), 420);
        }, 3500);
    }

    /* ── Pipeline step animtor ───────────────────────────── */
    let pipeTimer = null;

    function startPipeline() {
        if (!pipelineSteps) return;
        pipelineSteps.classList.add('visible');
        const steps = [1, 2, 3, 4];
        const delays = [0, 1200, 2400, 3600];
        steps.forEach((s, i) => {
            const dot = document.getElementById(`step-dot-${s}`);
            const conn = document.getElementById(`step-conn-${s}`);
            // Reset
            dot.classList.remove('active', 'done');
            if (conn) conn.classList.remove('done');
        });
        // Animate active step progressively
        delays.forEach((d, i) => {
            setTimeout(() => {
                const s = steps[i];
                const dot = document.getElementById(`step-dot-${s}`);
                // Mark previous as done
                if (i > 0) {
                    const prev = steps[i - 1];
                    document.getElementById(`step-dot-${prev}`).classList.replace('active', 'done');
                    const conn = document.getElementById(`step-conn-${prev}`);
                    if (conn) conn.classList.add('done');
                }
                dot.classList.add('active');
            }, d);
        });
    }

    function finishPipeline() {
        [1, 2, 3, 4].forEach(s => {
            const dot = document.getElementById(`step-dot-${s}`);
            const conn = document.getElementById(`step-conn-${s}`);
            if (dot) { dot.classList.remove('active'); dot.classList.add('done'); }
            if (conn) conn.classList.add('done');
        });
    }

    function resetPipeline() {
        if (!pipelineSteps) return;
        pipelineSteps.classList.remove('visible');
        [1, 2, 3, 4].forEach(s => {
            const dot = document.getElementById(`step-dot-${s}`);
            const conn = document.getElementById(`step-conn-${s}`);
            if (dot) dot.classList.remove('active', 'done');
            if (conn) conn.classList.remove('done');
        });
    }

    /* ── Image preview ───────────────────────────────────── */
    function showPreview(file) {
        if (!previewStrip) return;
        const url = URL.createObjectURL(file);
        previewThumb.src = url;
        previewName.textContent = file.name;
        previewSize.textContent = (file.size / 1024).toFixed(1) + ' KB';
        previewStrip.classList.add('visible');
    }

    /* ── File input (drop-zone click) ────────────────────── */
    dropZone.addEventListener('click', (e) => {
        if (e.target !== fileInput) fileInput.click();
    });
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            showPreview(e.target.files[0]);
            uploadFile(e.target.files[0]);
        }
    });

    /* ── Camera button ───────────────────────────────────── */
    cameraBtn.addEventListener('click', () => cameraInput.click());
    cameraInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            showPreview(e.target.files[0]);
            uploadFile(e.target.files[0]);
        }
    });

    /* ── Drag & Drop ─────────────────────────────────────── */
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('drag-active');
    });
    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('drag-active');
    });
    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('drag-active');
        if (e.dataTransfer.files.length > 0) {
            showPreview(e.dataTransfer.files[0]);
            uploadFile(e.dataTransfer.files[0]);
        }
    });

    /* ── CSV export ──────────────────────────────────────── */
    function csvEscape(v) {
        const s = (v ?? '').toString();
        return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
    }

    if (exportBtn) {
        exportBtn.addEventListener('click', () => {
            if (!lastInfo) return;
            const cols = ['Comercio', 'Fecha', 'Moneda', 'Impuestos', 'Total'];
            const header = cols.join(',');
            const row = cols.map((c) => csvEscape(lastInfo[c] || '')).join(',');
            const blob = new Blob(['\uFEFF' + header + '\n' + row + '\n'], { type: 'text/csv;charset=utf-8;' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `factura_${Date.now()}.csv`;
            a.click();
            URL.revokeObjectURL(url);
            showToast('CSV Exportado', 'Archivo descargado correctamente.');
        });
    }

    /* ── Helpers ─────────────────────────────────────────── */
    function showError(msg) {
        errorMsg.textContent = msg;
        errorMsg.style.display = 'block';
        showToast('Error al procesar', msg, 'error');
    }
    function clearError() {
        errorMsg.textContent = '';
        errorMsg.style.display = 'none';
    }
    function setLoading(active) {
        loader.style.display    = active ? 'block' : 'none';
        statusMsg.style.display = active ? 'block' : 'none';
    }

    /* ── Upload ──────────────────────────────────────────── */
    function uploadFile(file) {
        clearError();
        resultsContainer.classList.remove('visible');
        elements.confBadge.style.display = 'none';
        elements.statBlocks.innerHTML = '';
        elements.statConf.innerHTML = '';
        setLoading(true);
        startPipeline();

        const formData = new FormData();
        formData.append('file', file);

        fetch('/upload', { method: 'POST', body: formData })
            .then(async (response) => {
                const data = await response.json();
                setLoading(false);

                if (!response.ok || data.error) {
                    resetPipeline();
                    showError(data.error || 'Error desconocido en el procesamiento.');
                    return;
                }
                if (!data.images || !data.parsed_info) {
                    resetPipeline();
                    showError('Respuesta inesperada del servidor.');
                    return;
                }

                finishPipeline();

                elements.original.src  = data.images.original  + '?t=' + Date.now();
                elements.edge.src      = data.images.edge       + '?t=' + Date.now();
                elements.scan.src      = data.images.scan       + '?t=' + Date.now();
                elements.detection.src = data.images.detection  + '?t=' + Date.now();

                const info = data.parsed_info;
                lastInfo = info;
                elements.merchant.textContent = info.Comercio  || '---';
                elements.date.textContent     = info.Fecha     || '---';
                elements.currency.textContent = info.Moneda    || '---';
                elements.tax.textContent      = info.Impuestos || '---';
                elements.total.textContent    = info.Total     || '---';
                elements.raw.textContent      = data.text;

                const conf   = data.ocr_confidence ?? null;
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
                showToast(
                    'Factura procesada',
                    `${blocks || '?'} bloques OCR · Confianza ${conf || '?'}% · Total: ${info.Total || '---'}`,
                    'success'
                );
            })
            .catch(() => {
                setLoading(false);
                resetPipeline();
                showError('Error de conexión. Verifica que el servidor esté activo.');
            });
    }
});
