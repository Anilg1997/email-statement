document.addEventListener('DOMContentLoaded', function() {
  chrome.storage.local.get(['accountId', 'bankUrl'], function(r) {
    if (r.accountId) document.getElementById('accountId').value = r.accountId;
    if (r.bankUrl) document.getElementById('bankUrl').value = r.bankUrl;
  });
  document.getElementById('saveBtn').addEventListener('click', function() {
    const accountId = document.getElementById('accountId').value.trim();
    const bankUrl = document.getElementById('bankUrl').value.trim();
    const s = document.getElementById('status');
    if (!accountId || !bankUrl) { showStatus('Fill all fields', 'error'); return; }
    chrome.storage.local.set({ accountId, bankUrl }, function() {
      chrome.runtime.sendMessage({ type: 'updateSettings', accountId, bankUrl }, function(resp) {
        showStatus(resp && resp.success ? 'Saved! Rule updated.' : 'Saved but rule failed.', resp && resp.success ? 'success' : 'error');
      });
    });
  });
  function showStatus(msg, type) {
    const s = document.getElementById('status');
    s.textContent = msg; s.className = type;
    setTimeout(() => s.style.display = 'none', 3000);
  }
});
