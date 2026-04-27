document.addEventListener('DOMContentLoaded', () => {
    const fileInput = document.getElementById('file-input');
    const dropZone = document.getElementById('drop-zone');
    const loader = document.getElementById('loader');
    const statusMsg = document.getElementById('status-msg');
    const resultsContainer = document.getElementById('results-container');

    const elements = {
        original: document.getElementById('img-original'),
        edge: document.getElementById('img-edge'),
        scan: document.getElementById('img-scan'),
        detection: document.getElementById('img-detection'),
        date: document.getElementById('val-date'),
        currency: document.getElementById('val-currency'),
        total: document.getElementById('val-total'),
        raw: document.getElementById('text-raw')
    };

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) uploadFile(e.target.files[0]);
    });

    function uploadFile(file) {
        const formData = new FormData();
        formData.append('file', file);

        loader.style.display = 'block';
        statusMsg.style.display = 'block';
        resultsContainer.classList.remove('visible');

        fetch('/upload', { method: 'POST', body: formData })
        .then(response => response.json())
        .then(data => {
            loader.style.display = 'none';
            statusMsg.style.display = 'none';
            
            elements.original.src = data.images.original;
            elements.edge.src = data.images.edge;
            elements.scan.src = data.images.scan;
            elements.detection.src = data.images.detection;
            elements.date.textContent = data.parsed_info.Fecha;
            elements.currency.textContent = data.parsed_info.Moneda;
            elements.total.textContent = data.parsed_info.Total;
            elements.raw.textContent = data.text;

            resultsContainer.classList.add('visible');
        })
        .catch(err => {
            loader.style.display = 'none';
            statusMsg.style.display = 'none';
            alert('Error en el procesamiento.');
        });
    }

    // Drag & Drop
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.style.borderColor = 'var(--primary)';
    });
    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        if (e.dataTransfer.files.length > 0) uploadFile(e.dataTransfer.files[0]);
    });
});
