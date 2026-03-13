// =========================================
//  INVENTRA — shared_inventory.js
//  static/js/shared_inventory.js
// =========================================

// ---- Helpers ----

function showMsg(id, text) {
  const el = document.getElementById(id);
  if (!el) return;
  el.innerText = text;
  el.classList.add('show');
  setTimeout(() => { el.classList.remove('show'); el.innerText = ''; }, 3500);
}

function showPanelError(text) {
  const el = document.getElementById('panelError');
  el.innerText = text;
  el.classList.add('show');
}

// ---- Panel ----

function openEditPanel(id, name, qty, restock, desc) {
  document.getElementById('panelItemId').value = id;
  document.getElementById('panelName').value = name;
  document.getElementById('panelQty').value = qty;
  document.getElementById('panelRestock').value = restock ?? '';
  document.getElementById('panelDesc').value = desc;
  document.getElementById('panelError').classList.remove('show');

  document.getElementById('panel').classList.add('open');
  document.getElementById('overlay').classList.add('open');
  document.body.style.overflow = 'hidden';
}

function closePanel() {
  document.getElementById('panel').classList.remove('open');
  document.getElementById('overlay').classList.remove('open');
  document.body.style.overflow = '';
}

// ---- Submit Edit ----

function submitEdit() {
  const itemId   = document.getElementById('panelItemId').value;
  const name     = document.getElementById('panelName').value.trim();
  const qty      = document.getElementById('panelQty').value.trim();
  const restock  = document.getElementById('panelRestock').value.trim();
  const desc     = document.getElementById('panelDesc').value.trim();

  if (!name || qty === '') {
    showPanelError('Item name and quantity are required.');
    return;
  }

  const payload = {
    itemid:      itemId,
    itemName:    name,
    quantity:    qty,
    restockmin:  restock || null,
    description: desc
  };

  fetch('/edit_shared_row', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
  .then(async res => {
    const data = await res.json().catch(() => null);
    if (!res.ok) {
      showPanelError(data?.error || 'Failed to update item.');
      return;
    }
    closePanel();
    showMsg('successMsg', 'Item updated successfully.');
    // Reload page to reflect changes
    setTimeout(() => location.reload(), 1000);
  })
  .catch(() => showPanelError('Network error. Try again.'));
}
