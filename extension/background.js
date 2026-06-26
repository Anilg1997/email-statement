const RULE_ID = 1;

async function updateRedirectRule(accountId, bankUrl) {
  if (!accountId || !bankUrl) return;
  await chrome.declarativeNetRequest.updateDynamicRules({ removeRuleIds: [RULE_ID] });

  let urlFilter = bankUrl.replace(/\/+$/, '') + '/*';

  await chrome.declarativeNetRequest.updateDynamicRules({
    addRules: [{
      id: RULE_ID,
      priority: 1,
      action: {
        type: 'redirect',
        redirect: {
          regexSubstitution: 'http://localhost:8080/api/statements/replace?accountId=' + accountId + '&url=\\0'
        }
      },
      condition: {
        regexFilter: '^' + escapeRegex(urlFilter) + '.*\\.pdf([?#].*)?$',
        resourceTypes: ['main_frame', 'sub_frame', 'object', 'other']
      }
    }]
  });
}

function escapeRegex(url) {
  return url.replace(/[.*+?^${}()|[\]\\]/g, '\\$&').replace(/\*/g, '.*');
}

chrome.runtime.onStartup.addListener(async () => {
  const s = await chrome.storage.local.get(['accountId', 'bankUrl']);
  if (s.accountId && s.bankUrl) await updateRedirectRule(s.accountId, s.bankUrl);
});

chrome.runtime.onInstalled.addListener(async () => {
  const s = await chrome.storage.local.get(['accountId', 'bankUrl']);
  if (s.accountId && s.bankUrl) await updateRedirectRule(s.accountId, s.bankUrl);
});

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.type === 'updateSettings') {
    updateRedirectRule(msg.accountId, msg.bankUrl)
      .then(() => sendResponse({ success: true }))
      .catch(err => sendResponse({ success: false, error: err.message }));
    return true;
  }
});
