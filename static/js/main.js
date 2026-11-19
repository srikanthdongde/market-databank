/**
 * Market Databank Generation & Sharing Platform
 * Client-Side JavaScript Enhancements
 */

document.addEventListener('DOMContentLoaded', function () {
  // 1. Initialize Bootstrap Tooltips
  const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
  tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
  });

  // 2. Auto-dismiss Alert Messages after 5 seconds
  const autoAlerts = document.querySelectorAll('.alert-dismissible');
  autoAlerts.forEach(function (alert) {
    setTimeout(function () {
      const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
      if (bsAlert) {
        bsAlert.close();
      }
    }, 5000);
  });

  // 3. Client-side File Upload Validation & Feedback
  const fileInput = document.querySelector('input[type="file"][accept*=".csv"]');
  if (fileInput) {
    fileInput.addEventListener('change', function (e) {
      const file = e.target.files[0];
      const feedbackEl = document.getElementById('file-upload-feedback');
      
      if (!file) return;

      const maxBytes = 10 * 1024 * 1024; // 10MB
      const filename = file.name;

      if (!filename.toLowerCase().endsWith('.csv')) {
        alert('Invalid file format! Please select a valid .csv (Comma-Separated Values) file.');
        fileInput.value = '';
        if (feedbackEl) feedbackEl.innerHTML = '';
        return;
      }

      if (file.size > maxBytes) {
        const sizeMb = (file.size / (1024 * 1024)).toFixed(1);
        alert(`File is too large (${sizeMb} MB). Maximum allowed upload size is 10 MB.`);
        fileInput.value = '';
        if (feedbackEl) feedbackEl.innerHTML = '';
        return;
      }

      if (feedbackEl) {
        const sizeKb = (file.size / 1024).toFixed(1);
        feedbackEl.innerHTML = `
          <div class="alert alert-info py-2 px-3 mt-2 d-flex align-items-center gap-2 small">
            <i class="bi bi-filetype-csv fs-5"></i>
            <div>
              <strong>${file.name}</strong> (${sizeKb} KB) ready for parsing & verification.
            </div>
          </div>
        `;
      }
    });
  }

  // 4. Copy Column Headers to Clipboard
  const copyBtn = document.getElementById('btn-copy-columns');
  if (copyBtn) {
    copyBtn.addEventListener('click', function () {
      const colText = this.getAttribute('data-columns');
      if (colText) {
        navigator.clipboard.writeText(colText).then(function () {
          const originalHtml = copyBtn.innerHTML;
          copyBtn.innerHTML = '<i class="bi bi-check2"></i> Copied!';
          copyBtn.classList.replace('btn-outline-secondary', 'btn-success');
          setTimeout(function () {
            copyBtn.innerHTML = originalHtml;
            copyBtn.classList.replace('btn-success', 'btn-outline-secondary');
          }, 2000);
        });
      }
    });
  }
});
