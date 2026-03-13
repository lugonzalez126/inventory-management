// =========================================
//  INVENTRA — inventory.js
//  static/js/inventory.js
// =========================================

// ---- Helpers ----

function showMsg(id, text) {
  const el = document.getElementById(id);
  if (!el) return;
  el.innerText = text;
  el.classList.add('show');
  setTimeout(() => { el.classList.remove('show'); el.innerText = ''; }, 3500);
}

function showInline(id, text) {
  const el = document.getElementById(id);
  if (!el) return;
  el.innerText = text;
  el.style.display = 'block';
  setTimeout(() => { el.style.display = 'none'; el.innerText = ''; }, 3500);
}

// ---- Stats ----

function updateStats(items) {
  const total = items.length;
  const totalQty = items.reduce((sum, i) => sum + (i.quantity || 0), 0);
  const lowStock = items.filter(i =>
    i.restockmin !== null && i.restockmin !== undefined && i.quantity < i.restockmin
  ).length;

  document.getElementById('statTotal').innerText = total;
  document.getElementById('statQty').innerText = totalQty;
  document.getElementById('statLow').innerText = lowStock;

  const lowCard = document.getElementById('statLowCard');
  if (lowStock === 0) {
    lowCard.classList.add('hidden');
  } else {
    lowCard.classList.remove('hidden');
  }
}

// ---- Render Table ----

function renderTable(items) {
  const tbody = document.getElementById('invBody');
  tbody.innerHTML = '';

  if (items.length === 0) {
    tbody.innerHTML = `
      <tr id="emptyRow">
        <td colspan="6" style="text-align:center; color:var(--muted); padding:40px;">
          No items yet. Add your first item above.
        </td>
      </tr>`;
    return;
  }

  items.forEach(item => {
    const isLow = item.restockmin !== null &&
                  item.restockmin !== undefined &&
                  item.quantity < item.restockmin;

    let statusBadge;
    if (item.restockmin === null || item.restockmin === undefined) {
      statusBadge = `<span class="status-badge status-na">—</span>`;
    } else if (isLow) {
      statusBadge = `<span class="status-badge status-low">Low stock</span>`;
    } else {
      statusBadge = `<span class="status-badge status-ok">In stock</span>`;
    }

    const row = document.createElement('tr');
    if (isLow) row.classList.add('low-stock');

    row.innerHTML = `
      <td>${escapeHtml(item.itemName)}</td>
      <td>${item.quantity}</td>
      <td>${item.restockmin ?? '—'}</td>
      <td style="color:var(--muted); font-size:13px;">${escapeHtml(item.description || '')}</td>
      <td>${statusBadge}</td>
      <td>
        <button class="btn btn-ghost" style="font-size:12px; padding:5px 12px;"
          onclick="openEditPanel(${item.id}, '${escapeAttr(item.itemName)}', ${item.quantity}, ${item.restockmin ?? 'null'}, '${escapeAttr(item.description || '')}')">
          Edit
        </button>
      </td>`;

    tbody.appendChild(row);
  });
}

// ---- Fetch Inventory ----

function loadInventory() {
  fetch('/getUserInventory', { method: 'GET' })
    .then(res => res.json())
    .then(data => {
      const items = data.user_inventory || [];
      renderTable(items);
      updateStats(items);
    })
    .catch(() => showMsg('errorMsg', 'Failed to load inventory.'));
}

// ---- Panel ----

let panelMode = 'add'; // 'add' or 'edit'

function openAddPanel() {
  panelMode = 'add';
  document.getElementById('panelTitle').innerText = 'Add item';
  document.getElementById('panelSubmit').innerText = 'Save item';
  document.getElementById('panelItemId').value = '';
  document.getElementById('panelName').value = '';
  document.getElementById('panelQty').value = '';
  document.getElementById('panelRestock').value = '';
  document.getElementById('panelDesc').value = '';
  document.getElementById('panelError').classList.remove('show');
  openPanel();
}

function openEditPanel(id, name, qty, restock, desc) {
  panelMode = 'edit';
  document.getElementById('panelTitle').innerText = 'Edit item';
  document.getElementById('panelSubmit').innerText = 'Save changes';
  document.getElementById('panelItemId').value = id;
  document.getElementById('panelName').value = name;
  document.getElementById('panelQty').value = qty;
  document.getElementById('panelRestock').value = restock ?? '';
  document.getElementById('panelDesc').value = desc;
  document.getElementById('panelError').classList.remove('show');
  openPanel();
}

function openPanel() {
  document.getElementById('panel').classList.add('open');
  document.getElementById('overlay').classList.add('open');
  document.body.style.overflow = 'hidden';
}

function closePanel() {
  document.getElementById('panel').classList.remove('open');
  document.getElementById('overlay').classList.remove('open');
  document.body.style.overflow = '';
}

function submitPanel() {
  const name     = document.getElementById('panelName').value.trim();
  const qty      = document.getElementById('panelQty').value.trim();
  const restock  = document.getElementById('panelRestock').value.trim();
  const desc     = document.getElementById('panelDesc').value.trim();
  const itemId   = document.getElementById('panelItemId').value;

  if (!name || qty === '') {
    showPanelError('Item name and quantity are required.');
    return;
  }

  const payload = {
    itemName:   name,
    quantity:   qty,
    restockmin: restock || null,
    description: desc
  };

  if (panelMode === 'edit') {
    payload.itemid = itemId;
  }

  const url    = panelMode === 'add' ? '/add_row' : '/edit_row';
  const method = panelMode === 'add' ? 'POST' : 'PUT';

  fetch(url, {
    method,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
  .then(async res => {
    const data = await res.json().catch(() => null);
    if (!res.ok) {
      showPanelError(data?.error || 'Something went wrong.');
      return;
    }
    closePanel();
    showMsg('successMsg', panelMode === 'add' ? 'Item added.' : 'Item updated.');
    loadInventory();
  })
  .catch(() => showPanelError('Network error. Try again.'));
}

function showPanelError(text) {
  const el = document.getElementById('panelError');
  el.innerText = text;
  el.classList.add('show');
}

// ---- Share ----

function shareInventory() {
  const username = document.getElementById('shareInput').value.trim();
  if (!username) {
    showInline('shareError', 'Enter a username to share with.');
    return;
  }

  fetch('/share_inv', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username })
  })
  .then(async res => {
    const data = await res.json().catch(() => null);
    if (!res.ok) {
      showInline('shareError', data?.error || 'Share failed.');
      return;
    }
    document.getElementById('shareInput').value = '';
    showInline('shareSuccess', `Inventory shared with ${username}.`);
  })
  .catch(() => showInline('shareError', 'Network error. Try again.'));
}

// ---- Escape helpers (prevent XSS) ----

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function escapeAttr(str) {
  return String(str).replace(/'/g, "\\'").replace(/"/g, '&quot;');
}

// ---- Init ----
loadInventory();
