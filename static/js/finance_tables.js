function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(';').shift();
  return '';
}

async function postJson(url, payload) {
  const csrfToken = getCookie('csrftoken');
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': csrfToken,
    },
    body: JSON.stringify(payload),
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const message = data.error || 'Request failed';
    throw new Error(message);
  }
  return data;
}

function initInlineEditing() {
  document.querySelectorAll('[data-editable="true"]').forEach((cell) => {
    if (cell.matches('input, select, textarea')) {
      cell.addEventListener('change', async () => {
        const row = cell.closest('tr');
        if (!row || row.dataset.locked === 'true') return;
        const url = row.dataset.updateUrl;
        if (!url) return;
        try {
          await postJson(url, {
            field: cell.dataset.field,
            value: cell.value,
          });
          row.classList.add('saved');
        } catch (err) {
          alert(err.message);
        }
      });
    } else {
      cell.addEventListener('blur', async () => {
        const row = cell.closest('tr');
        if (!row || row.dataset.locked === 'true') return;
        const url = row.dataset.updateUrl;
        if (!url) return;
        try {
          await postJson(url, {
            field: cell.dataset.field,
            value: cell.textContent.trim(),
          });
          row.classList.add('saved');
        } catch (err) {
          alert(err.message);
        }
      });
    }
  });
}

function initAddRow() {
  document.querySelectorAll('[data-add-row]').forEach((button) => {
    button.addEventListener('click', async () => {
      const wrapper = button.closest('[data-add-row-wrapper]') || document;
      const row = wrapper.querySelector('[data-new-row="true"]');
      if (!row) return;
      const url = row.dataset.createUrl;
      if (!url) return;

      const payload = {};
      row.querySelectorAll('[data-field]').forEach((fieldEl) => {
        if (fieldEl.matches('input, select, textarea')) {
          payload[fieldEl.dataset.field] = fieldEl.value;
        } else {
          payload[fieldEl.dataset.field] = fieldEl.textContent.trim();
        }
      });

      try {
        await postJson(url, payload);
        window.location.reload();
      } catch (err) {
        alert(err.message);
      }
    });
  });
}

function initPostButtons() {
  document.querySelectorAll('[data-post-url]').forEach((button) => {
    button.addEventListener('click', async () => {
      const url = button.dataset.postUrl;
      if (!url) return;
      try {
        await postJson(url, {});
        window.location.reload();
      } catch (err) {
        alert(err.message);
      }
    });
  });
}

function initFinanceTables() {
  initInlineEditing();
  initAddRow();
  initPostButtons();
}

document.addEventListener('DOMContentLoaded', initFinanceTables);
