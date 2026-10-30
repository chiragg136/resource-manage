// Resource Management System - Enterprise App Logic
const API_BASE = '/api';
const API = {
  async get(endpoint) {
    const res = await fetch(API_BASE + endpoint);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },
  async post(endpoint, data) {
    const res = await fetch(API_BASE + endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },
  async put(endpoint, data) {
    const res = await fetch(API_BASE + endpoint, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },
  async delete(endpoint) {
    const res = await fetch(API_BASE + endpoint, { method: 'DELETE' });
    if (!res.ok) throw new Error(await res.text());
    if (res.status === 204) return null;
    return res.json();
  }
};

// --- Modals ---
function openModal(id) {
  const m = document.getElementById(id);
  if (m) {
    m.classList.add('show');
    // small delay to prevent double clicks
    setTimeout(() => {
      document.body.style.overflow = 'hidden';
    }, 10);
  }
}
function closeModal(id) {
  const m = document.getElementById(id);
  if (m) {
    m.classList.remove('show');
    document.body.style.overflow = '';
  }
}

// Close modals on clicking backdrop
document.addEventListener('click', e => {
  if (e.target.classList.contains('modal-backdrop')) {
    e.target.classList.remove('show');
    document.body.style.overflow = '';
  }
});


// --- Custom Confirm Dialog ---
// We inject a global confirm modal into the DOM if it doesn't exist
function initConfirmModal() {
  if (document.getElementById('confirm-modal')) return;
  const html = `
    <div class="modal-backdrop" id="confirm-modal">
      <div class="modal-content modal-sm">
        <div class="modal-header">
          <div class="modal-title" id="confirm-title">Confirm Action</div>
          <button class="btn-close" onclick="closeConfirm()">×</button>
        </div>
        <div class="modal-body">
          <p id="confirm-message" style="margin:0; font-size:14px;"></p>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" onclick="closeConfirm()">Cancel</button>
          <button class="btn btn-danger" id="confirm-btn">Confirm</button>
        </div>
      </div>
    </div>
  `;
  document.body.insertAdjacentHTML('beforeend', html);
}

let confirmCallback = null;
function showConfirm(message, callback, title="Confirm Delete") {
  initConfirmModal();
  document.getElementById('confirm-title').textContent = title;
  document.getElementById('confirm-message').textContent = message;
  
  const btn = document.getElementById('confirm-btn');
  // Reset button state
  btn.disabled = false;
  btn.innerHTML = 'Confirm';
  
  btn.onclick = async () => {
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Processing...';
    try {
      await callback();
    } finally {
      closeConfirm();
    }
  };
  openModal('confirm-modal');
}
function closeConfirm() {
  closeModal('confirm-modal');
}


// --- Toasts ---
function showToast(message, type = 'success') {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    document.body.appendChild(container);
  }

  let icon = 'fa-check-circle';
  if (type === 'error') icon = 'fa-exclamation-circle';
  if (type === 'warning') icon = 'fa-exclamation-triangle';
  if (type === 'info') icon = 'fa-info-circle';

  const t = document.createElement('div');
  t.className = `toast ${type}`;
  t.innerHTML = `<i class="fas ${icon}"></i> <div>${message}</div>`;
  
  container.appendChild(t);
  setTimeout(() => {
    t.style.opacity = '0';
    setTimeout(() => t.remove(), 300);
  }, 3000);
}


// --- Formatters ---
function fmtDate(dateStr) {
  if (!dateStr) return '—';
  const d = new Date(dateStr);
  return d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' });
}
function fmtDateTime(dateStr) {
  if (!dateStr) return '—';
  const d = new Date(dateStr);
  return d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })
    + ', ' + d.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', hour12: true });
}
function fmtCurrency(val) {
  if (val == null) return '—';
  return '₹' + Number(val).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}
function monthName(m) {
  const arr = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
  return arr[m-1] || m;
}

// --- Search Filter ---
function filterTable(data, query) {
  if (!query) return data;
  query = query.toLowerCase();
  return data.filter(item => {
    return Object.values(item).some(val => 
      String(val).toLowerCase().includes(query)
    );
  });
}

// --- Badges ---
function invoiceStatusBadge(status) {
  if (status === 'Paid') return '<span class="badge badge-success">Paid</span>';
  if (status === 'Overdue') return '<span class="badge badge-danger">Overdue</span>';
  if (status === 'Submitted') return '<span class="badge badge-primary">Submitted</span>';
  return '<span class="badge badge-secondary">Draft</span>';
}
function paymentStatusBadge(status) {
  if (status === 'Received') return '<span class="badge badge-success">Received</span>';
  if (status === 'Partial') return '<span class="badge badge-warning">Partial</span>';
  return '<span class="badge badge-secondary">Pending</span>';
}
    
    // --- Mass Import Global Logic ---
    let validImportRecords = [];

    function openImportModal(module) {
      document.getElementById('import-title').textContent =
        'Import ' + module.charAt(0).toUpperCase() + module.slice(1);
      document.getElementById('import-file').value = '';
      document.getElementById('import-preview-table').style.display = 'none';
      document.getElementById('import-status').innerHTML = '';
      document.getElementById('import-confirm-btn').disabled = true;
      document.getElementById('import-template-link').href =
        '/import/template/' + module + '?format=xlsx';
      window.currentImportModule = module;
      window.currentImportErrors = [];
      validImportRecords = [];
      openModal('import-modal');
    }

    async function previewImport(event) {
      const file = event.target.files[0];
      if (!file) return;

      const formData = new FormData();
      formData.append('file', file);

      document.getElementById('import-status').innerHTML =
        '<i class="fa-solid fa-spinner fa-spin"></i> Analyzing file…';
      document.getElementById('import-preview-table').style.display = 'none';
      document.getElementById('import-confirm-btn').disabled = true;
      validImportRecords = [];

      try {
        const response = await fetch('/import/preview/' + window.currentImportModule, {
          method: 'POST',
          body: formData
        });

        if (!response.ok) {
          const err = await response.json();
          throw new Error(err.detail || 'Preview failed');
        }

        const data = await response.json();
        const records = data.records;
        const total = records.length;

        validImportRecords = records.filter(r => r.is_valid).map(r => r.payload);
        const validCount   = validImportRecords.length;
        const invalidCount = total - validCount;

        // Classify invalid rows: duplicates vs other errors
        const dupKeywords  = ['already exists', 'duplicated within'];
        const dupRows      = records.filter(r =>
          !r.is_valid && r.errors.some(e => dupKeywords.some(k => e.toLowerCase().includes(k)))
        );
        const errRows      = records.filter(r =>
          !r.is_valid && !r.errors.some(e => dupKeywords.some(k => e.toLowerCase().includes(k)))
        );

        window.currentImportErrors = records.filter(r => !r.is_valid);

        // Status bar
        let statusHtml =
          `<span style="color:#28a745;font-weight:600;">✔ ${validCount} will be imported</span>` +
          (dupRows.length   ? ` &nbsp;|&nbsp; <span style="color:#e67e22;font-weight:600;">⊘ ${dupRows.length} duplicate(s) skipped</span>` : '') +
          (errRows.length   ? ` &nbsp;|&nbsp; <span style="color:#dc3545;font-weight:600;">✖ ${errRows.length} error(s)</span>` : '');

        if (invalidCount > 0) {
          statusHtml +=
            `&nbsp; <button class="btn btn-sm btn-outline-danger"
               style="padding:2px 8px;font-size:11px;margin-left:6px;"
               onclick="downloadErrors()">
               <i class="fa-solid fa-download"></i> Download Failed Rows
             </button>`;
        }
        document.getElementById('import-status').innerHTML = statusHtml;
        document.getElementById('import-confirm-btn').disabled = validCount === 0;

        // Preview table
        if (total > 0) {
          const keys = Object.keys(records[0].raw_data);
          document.getElementById('import-preview-head').innerHTML =
            '<tr><th>Row</th><th>Status</th>' +
            keys.map(k => `<th>${k}</th>`).join('') +
            '<th>Reason</th></tr>';

          document.getElementById('import-preview-body').innerHTML =
            records.map(r => {
              const isDup = !r.is_valid &&
                r.errors.some(e => dupKeywords.some(k => e.toLowerCase().includes(k)));
              const badge = r.is_valid
                ? '<span class="badge" style="background:#28a745;color:#fff;">✔ Valid</span>'
                : isDup
                  ? '<span class="badge" style="background:#e67e22;color:#fff;">⊘ Duplicate</span>'
                  : '<span class="badge" style="background:#dc3545;color:#fff;">✖ Error</span>';
              const rowBg = r.is_valid ? '' :
                isDup ? 'background:#fff3cd;' : 'background:#ffe6e6;';
              const errTip = r.errors.join(' | ').replace(/"/g, '&quot;');
              const errTxt = r.errors.join('; ');
              return `<tr style="${rowBg}">
                <td style="font-size:11px;color:#666;">${r.row_index}</td>
                <td>${badge}</td>
                ${keys.map(k =>
                  `<td>${r.raw_data[k] !== null && r.raw_data[k] !== undefined ? r.raw_data[k] : ''}</td>`
                ).join('')}
                <td style="color:${r.is_valid ? '#28a745' : isDup ? '#e67e22' : '#dc3545'};
                            font-size:11px;max-width:220px;white-space:normal;"
                    title="${errTip}">${errTxt}</td>
              </tr>`;
            }).join('');

          document.getElementById('import-preview-table').style.display = 'table';
        }

      } catch (err) {
        document.getElementById('import-status').innerHTML =
          `<span class="text-danger"><i class="fa-solid fa-triangle-exclamation"></i> ${err.message}</span>`;
      }
    }

    function downloadErrors() {
      if (!window.currentImportErrors || window.currentImportErrors.length === 0) return;

      let csvContent = "data:text/csv;charset=utf-8,";
      const keys = Object.keys(window.currentImportErrors[0].raw_data);

      csvContent += keys.join(",") + ",Error Reasons\n";

      window.currentImportErrors.forEach(r => {
        let rowData = keys.map(k => {
          let val = r.raw_data[k] !== null && r.raw_data[k] !== undefined
            ? String(r.raw_data[k]) : "";
          if (val.includes(',') || val.includes('"')) {
            val = '"' + val.replace(/"/g, '""') + '"';
          }
          return val;
        });
        let errorStr = r.errors.join(' | ');
        if (errorStr.includes(',') || errorStr.includes('"')) {
          errorStr = '"' + errorStr.replace(/"/g, '""') + '"';
        }
        rowData.push(errorStr);
        csvContent += rowData.join(",") + "\n";
      });

      const encodedUri = encodeURI(csvContent);
      const link = document.createElement("a");
      link.setAttribute("href", encodedUri);
      link.setAttribute("download", `import_errors_${window.currentImportModule}.csv`);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }

    async function confirmImport() {
      if (validImportRecords.length === 0) return;

      const btn = document.getElementById('import-confirm-btn');
      btn.disabled = true;
      btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Importing…';

      try {
        const response = await fetch('/import/confirm/' + window.currentImportModule, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(validImportRecords)
        });

        if (!response.ok) {
          const err = await response.json();
          throw new Error(err.detail || 'Import failed');
        }

        const res = await response.json();

        // Build a clear result message
        let msg = `✔ ${res.inserted_count} record(s) imported successfully.`;
        if (res.skipped_count && res.skipped_count > 0) {
          msg += ` ⊘ ${res.skipped_count} duplicate(s) were skipped.`;
        }

        showToast(msg, res.inserted_count > 0 ? 'success' : 'warning');
        closeModal('import-modal');
        await loadAll();

      } catch (err) {
        showToast('Import failed: ' + err.message, 'error');
      } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fa-solid fa-check"></i> Confirm Import';
      }
    }
