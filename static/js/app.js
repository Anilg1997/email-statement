const API = 'http://localhost:8080/api';

// ========== TAB SWITCHING ==========
function switchTab(tabName){
  document.querySelectorAll('.sidebar-item').forEach(i=>i.classList.remove('active'));
  document.querySelectorAll('.tab-content').forEach(t=>t.classList.remove('active'));
  document.querySelector('.sidebar-item[data-tab="'+tabName+'"]').classList.add('active');
  document.getElementById('tab-'+tabName).classList.add('active');
  if(tabName==='upload') refreshList();
}
document.addEventListener('DOMContentLoaded',function(){
  document.querySelectorAll('.sidebar-item').forEach(item=>{
    item.addEventListener('click',function(){
      switchTab(this.dataset.tab);
    });
  });
  setupUpload();
  var hash=window.location.hash.replace('#','');
  if(hash) setTimeout(function(){switchTab(hash);},100);
  window.addEventListener('hashchange',function(){
    var h=window.location.hash.replace('#','');
    if(h) switchTab(h);
  });
});

// ========== UPLOAD ==========
function setupUpload(){
  var zone=document.getElementById('uploadZone');
  var input=document.getElementById('fileInput');
  if(!zone||!input) return;
  zone.addEventListener('click',function(){input.click();});
  zone.addEventListener('dragover',function(e){e.preventDefault();zone.classList.add('dragover');});
  zone.addEventListener('dragleave',function(){zone.classList.remove('dragover');});
  zone.addEventListener('drop',function(e){e.preventDefault();zone.classList.remove('dragover');
    if(e.dataTransfer.files.length) handleFile(e.dataTransfer.files[0]);});
  input.addEventListener('change',function(){if(input.files.length) handleFile(input.files[0]);});
}

function handleFile(file){
  if(file.type!=='application/pdf'&&!file.name.toLowerCase().endsWith('.pdf')){
    toast('Please select a PDF file','error');return;
  }
  document.getElementById('fileName').textContent=file.name+' ('+Math.round(file.size/1024)+' KB)';
  document.getElementById('fileInfo').style.display='flex';
  window._selectedFile=file;
}

function clearFile(){
  document.getElementById('fileInfo').style.display='none';
  document.getElementById('fileInput').value='';
  window._selectedFile=null;
}

function uploadPdf(){
  var accountId=document.getElementById('uploadAccountId').value.trim();
  var file=window._selectedFile;
  if(!accountId){toast('Enter Account ID','error');return;}
  if(!file){toast('Select a PDF file','error');return;}
  var status=document.getElementById('uploadStatus');
  status.textContent='Uploading...';status.className='upload-status';status.style.display='block';
  var fd=new FormData();fd.append('accountId',accountId);fd.append('file',file);
  fetch(API+'/upload',{method:'POST',body:fd})
  .then(function(r){return r.json();})
  .then(function(d){
    if(d.status==='ok'){
      status.textContent='\u2705 Uploaded successfully! Password: '+accountId.slice(-4);
      status.className='upload-status success';clearFile();refreshList();
      toast('PDF uploaded for account '+accountId,'success');
    } else { status.textContent='\u274C Error: '+d.message;status.className='upload-status error'; }
  })
  .catch(function(e){status.textContent='\u274C Error: '+e.message;status.className='upload-status error';});
}

function refreshList(){
  var tbody=document.getElementById('uploadListBody');
  if(!tbody) return;
  tbody.innerHTML='<tr><td colspan="4" style="text-align:center;padding:30px;color:#999">Loading...</td></tr>';
  fetch(API+'/list').then(function(r){return r.json();}).then(function(data){
    if(data.length===0){
      tbody.innerHTML='<tr><td colspan="4" style="text-align:center;padding:30px;color:#999">No uploads yet. Upload an edited PDF above.</td></tr>';
    } else {
      tbody.innerHTML='';
      data.forEach(function(item){
        var pw=item.accountId.length>=4?item.accountId.slice(-4):item.accountId;
        var tr=document.createElement('tr');
        tr.innerHTML='<td><strong>'+item.accountId+'</strong></td>'+
          '<td>'+item.file+'</td><td><code>'+pw+'</code></td>'+
          '<td><a href="'+API+'/replace?accountId='+item.accountId+'" target="_blank" class="btn btn-sm btn-outline" style="text-decoration:none">Open PDF</a></td>';
        tbody.appendChild(tr);
      });
    }
    document.getElementById('uploadCount').textContent=data.length+' file(s)';
  }).catch(function(e){tbody.innerHTML='<tr><td colspan="4" style="text-align:center;padding:30px;color:#dc2626">Error loading: '+e.message+'</td></tr>';});
}

// ========== TOAST NOTIFICATIONS ==========
function toast(msg,type){
  var t=document.getElementById('toast');t.textContent=msg;
  t.className='toast '+type+' show';
  clearTimeout(t._h);t._h=setTimeout(function(){t.classList.remove('show');},4000);
}

// ========== BGV VERIFICATION ==========

function switchBGVTab(tabName){
  document.querySelectorAll('.bgv-subtab').forEach(function(t){t.style.display='none';});
  document.getElementById('bgv-'+tabName).style.display='block';
}

function generateBGVLink(){
  var accountId=document.getElementById('bgvAccountId').value.trim();
  var bankName=document.getElementById('bgvBankName').value.trim();
  var holderName=document.getElementById('bgvHolderName').value.trim();
  var mode=document.getElementById('bgvMode').value;

  if(!accountId){toast('Enter Account ID','error');return;}
  if(!bankName){toast('Enter Bank Name','error');return;}

  toast('Generating verification link...','info');

  // First store default statement data for the portal viewer
  fetch(API+'/bgv/store-statement',{
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify({
      bankName: bankName,
      accountNumber: accountId,
      accountHolder: holderName,
      period: 'Monthly Statement',
      branch: 'Main Branch',
      ifsc: 'BANK0001234',
      address: 'Customer Address',
      openingBalance: '25000.00',
      totalDebits: '5000.00',
      totalCredits: '10000.00',
      closingBalance: '30000.00',
      transactions: []
    })
  })
  .then(function(){return fetch(API+'/bgv/generate-link',{
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify({
      accountId:accountId,
      bankName:bankName,
      accountHolder:holderName,
      mode:mode
    })
  });})
  .then(function(r){return r.json();})
  .then(function(data){
    if(data.status!=='ok') throw new Error(data.message||'Failed to generate link');

    document.getElementById('bgvViewUrl').textContent=data.viewUrl;
    document.getElementById('bgvPassword').textContent=data.password;
    document.getElementById('bgvVerificationId').textContent=data.verificationId;
    document.getElementById('bgvOpenLink').href=data.viewUrl;
    document.getElementById('bgvOpenPdf').href=API+'/replace?accountId='+accountId;
    document.getElementById('bgvLinkResult').style.display='block';

    document.getElementById('emailVerificationId').value=data.verificationId;

    toast('Verification link generated! Open it to see the portal view.','success');
  })
  .catch(function(e){
    toast('Failed: '+e.message,'error');
  });
}

function copyBGVUrl(){
  var url=document.getElementById('bgvViewUrl').textContent;
  if(navigator.clipboard){
    navigator.clipboard.writeText(url).then(function(){
      toast('URL copied to clipboard!','success');
    }).catch(function(){
      fallbackCopy(url);
    });
  } else {
    fallbackCopy(url);
  }
}

function fallbackCopy(text){
  var ta=document.createElement('textarea');
  ta.value=text;
  ta.style.position='fixed';ta.style.opacity='0';
  document.body.appendChild(ta);
  ta.select();
  document.execCommand('copy');
  document.body.removeChild(ta);
  toast('URL copied!','success');
}

function generateEmailTemplate(){
  var accountId=document.getElementById('emailAccountId').value.trim();
  var bankName=document.getElementById('emailBankName').value.trim();
  var holderName=document.getElementById('emailHolderName').value.trim();
  var toEmail=document.getElementById('emailTo').value.trim();
  var verificationId=document.getElementById('emailVerificationId').value.trim();

  if(!accountId){toast('Enter Account ID','error');return;}
  if(!bankName){toast('Enter Bank Name','error');return;}
  if(!holderName){toast('Enter Account Holder name','error');return;}
  if(!toEmail){toast('Enter BGV email address','error');return;}

  toast('Generating email template...','info');

  fetch(API+'/bgv/email-template',{
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify({
      accountId:accountId,
      bankName:bankName,
      accountHolder:holderName,
      toEmail:toEmail,
      verificationId:verificationId
    })
  })
  .then(function(r){return r.json();})
  .then(function(data){
    if(data.status!=='ok') throw new Error(data.message);

    document.getElementById('emailFrom').textContent=data.fromEmail;
    document.getElementById('emailSubject').textContent=data.subject;
    var preview=document.getElementById('emailPreview');
    preview.innerHTML='<iframe srcdoc="'+escapeHtmlAttr(data.htmlContent)+'" style="width:100%;height:420px;border:none;"></iframe>';
    document.getElementById('emailResult').style.display='block';

    toast('Email template generated! Preview below.','success');
  })
  .catch(function(e){
    toast('Failed: '+e.message,'error');
  });
}

function refreshBGVList(){
  var tbody=document.getElementById('bgvHistoryBody');
  if(!tbody) return;
  tbody.innerHTML='<tr><td colspan="7" style="text-align:center;padding:30px;color:#999">Loading...</td></tr>';

  fetch(API+'/bgv/links')
  .then(function(r){return r.json();})
  .then(function(data){
    if(!data || data.length===0){
      tbody.innerHTML='<tr><td colspan="7" style="text-align:center;padding:30px;color:#999">No verification links generated yet.</td></tr>';
    } else {
      tbody.innerHTML='';
      data.forEach(function(item){
        var statusBadge = item.status==='active'
          ? '<span style="background:#e8f4e8;color:#16a34a;padding:2px 10px;border-radius:10px;font-size:12px;font-weight:600;">Active</span>'
          : '<span style="background:#fee2e2;color:#dc2626;padding:2px 10px;border-radius:10px;font-size:12px;font-weight:600;">Expired</span>';

        var tr=document.createElement('tr');
        tr.innerHTML=
          '<td><code style="font-size:12px;">'+item.verificationId+'</code></td>'+
          '<td>'+item.accountId+'</td>'+
          '<td>'+item.bankName+'</td>'+
          '<td>'+statusBadge+'</td>'+
          '<td>'+item.accessCount+' time(s)'+(item.lastAccessedAt!=='-' ? '<br><span style="font-size:11px;color:#999">'+item.lastAccessedAt+'</span>' : '')+'</td>'+
          '<td style="font-size:12px;color:#666">'+item.createdAt+'</td>'+
          '<td><div style="display:flex;gap:6px;flex-wrap:wrap;">'+
            '<a href="'+item.viewUrl+'" target="_blank" class="btn btn-sm btn-primary" style="text-decoration:none">Open</a>'+
            '<button class="btn btn-sm btn-outline" onclick="copyText(\''+item.viewUrl+'\')">Copy</button>'+
          '</div></td>';
        tbody.appendChild(tr);
      });
    }
  })
  .catch(function(e){
    tbody.innerHTML='<tr><td colspan="7" style="text-align:center;padding:30px;color:#dc2626">Error: '+e.message+'</td></tr>';
  });
}

function escapeHtmlAttr(str){
  return str.replace(/&/g,'&amp;').replace(/\"/g,'&quot;').replace(/'/g,'&#39;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

function copyText(text){
  if(navigator.clipboard){
    navigator.clipboard.writeText(text).then(function(){
      toast('Copied!','success');
    }).catch(function(){fallbackCopy(text);});
  } else {
    fallbackCopy(text);
  }
}

// ========== EMAIL & TRACKING ==========

function saveEmailConfig(){
  var data={
    host:document.getElementById('smtpHost').value.trim(),
    port:parseInt(document.getElementById('smtpPort').value)||587,
    username:document.getElementById('smtpUsername').value.trim(),
    password:document.getElementById('smtpPassword').value.trim(),
    useSsl:document.getElementById('smtpUseSsl').checked,
    fromName:document.getElementById('smtpFromName').value.trim()
  };
  if(!data.host||!data.username||!data.password){
    toast('Fill in SMTP host, username, and password','error');return;
  }
  toast('Saving email configuration...','info');
  fetch(API+'/email/config',{
    method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)
  })
  .then(function(r){return r.json();})
  .then(function(d){
    var status=document.getElementById('emailConfigStatus');
    if(d.status==='ok'){
      status.textContent='\u2705 '+d.message;
      status.className='upload-status success';status.style.display='block';
      toast('Email configured successfully!','success');
    } else {
      status.textContent='\u274C '+d.message;
      status.className='upload-status error';status.style.display='block';
      toast('Failed to configure email','error');
    }
  })
  .catch(function(e){
    var status=document.getElementById('emailConfigStatus');
    status.textContent='\u274C Error: '+e.message;
    status.className='upload-status error';status.style.display='block';
    toast('Error saving config','error');
  });
}

function loadEmailConfig(){
  fetch(API+'/email/config')
  .then(function(r){return r.json();})
  .then(function(d){
    if(d.configured){
      var status=document.getElementById('emailConfigStatus');
      status.textContent='\u2705 Email configured: '+d.username+' via '+d.host+':'+d.port;
      status.className='upload-status success';status.style.display='block';
      if(d.host) document.getElementById('smtpHost').value=d.host;
      if(d.port) document.getElementById('smtpPort').value=d.port;
      if(d.username) document.getElementById('smtpUsername').value=d.username;
      if(d.fromName) document.getElementById('smtpFromName').value=d.fromName;
    }
  }).catch(function(){});
}

function sendStatementEmail(){
  var toEmail=document.getElementById('sendToEmail').value.trim();
  var accountId=document.getElementById('sendAccountId').value.trim();
  var bankName=document.getElementById('sendBankName').value.trim();
  var holderName=document.getElementById('sendHolderName').value.trim();

  if(!toEmail){toast('Enter recipient email address','error');return;}
  if(!accountId){toast('Enter Account ID','error');return;}
  if(!bankName){toast('Enter Bank Name','error');return;}

  var result=document.getElementById('sendEmailResult');
  result.textContent='Sending email with PDF attachment...';
  result.className='upload-status';result.style.display='block';
  toast('Sending email...','info');

  fetch(API+'/email/send',{
    method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({
      toEmail:toEmail,accountId:accountId,
      bankName:bankName,accountHolder:holderName
    })
  })
  .then(function(r){return r.json();})
  .then(function(d){
    if(d.status==='ok'){
      result.textContent='\u2705 '+d.message+' (Subject: '+d.subject+', Attachment: '+d.attachment+')';
      result.className='upload-status success';
      toast('Email sent successfully to '+toEmail+'!','success');
    } else {
      result.textContent='\u274C '+d.message;
      result.className='upload-status error';
      toast('Failed to send email','error');
    }
  })
  .catch(function(e){
    result.textContent='\u274C Error: '+e.message;
    result.className='upload-status error';
    toast('Error sending email','error');
  });
}

function refreshAccessLog(){
  var filter=document.getElementById('accessLogFilter');
  var accountId=filter?filter.value.trim():'';
  var url=API+'/access-log';
  if(accountId) url+='?accountId='+encodeURIComponent(accountId);

  var tbody=document.getElementById('accessLogBody');
  if(!tbody) return;
  tbody.innerHTML='<tr><td colspan="5" style="text-align:center;padding:30px;color:#999">Loading...</td></tr>';

  fetch(url)
  .then(function(r){return r.json();})
  .then(function(d){
    if(d.stats){
      var statsDiv=document.getElementById('accessLogStats');
      if(statsDiv){
        statsDiv.innerHTML='<div style="display:flex;gap:16px;flex-wrap:wrap;">'+
          '<div style="background:#f0f7ff;padding:12px 20px;border-radius:8px;"><strong>'+d.stats.totalAccesses+'</strong><br><span style="font-size:12px;color:#666;">Total Accesses</span></div>'+
          '<div style="background:#f0fdf4;padding:12px 20px;border-radius:8px;"><strong>'+d.stats.uniqueAccounts+'</strong><br><span style="font-size:12px;color:#666;">Unique Accounts</span></div>'+
          '</div>';
        statsDiv.style.display='block';
      }
    }

    var logs=d.logs||[];
    if(logs.length===0){
      tbody.innerHTML='<tr><td colspan="5" style="text-align:center;padding:30px;color:#999">No access logs yet. PDFs will be tracked when accessed via the Replace endpoint or Chrome Extension.</td></tr>';
    } else {
      tbody.innerHTML='';
      logs.forEach(function(log){
        var tr=document.createElement('tr');
        var srcColor=log.source==='direct'?'#f59e0b':'#16a34a';
        tr.innerHTML='<td style="font-size:12px;white-space:nowrap;">'+log.timestamp+'</td>'+
          '<td><strong>'+log.accountId+'</strong></td>'+
          '<td style="font-size:12px;">'+log.ipAddress+'</td>'+
          '<td><span style="background:'+srcColor+'20;color:'+srcColor+';padding:2px 8px;border-radius:4px;font-size:11px;font-weight:600;">'+log.source+'</span></td>'+
          '<td style="font-size:11px;color:#999;max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" title="'+escapeHtmlAttr(log.userAgent)+'">'+log.userAgent+'</td>';
        tbody.appendChild(tr);
      });
    }
  })
  .catch(function(e){
    tbody.innerHTML='<tr><td colspan="5" style="text-align:center;padding:30px;color:#dc2626">Error: '+e.message+'</td></tr>';
  });
}

// ========== INBOUND BGV EMAIL AUTO-RESPONDER ==========

function saveInboundConfig(){
  var data={
    imapHost:document.getElementById('inImapHost').value.trim(),
    imapPort:parseInt(document.getElementById('inImapPort').value)||993,
    imapUsername:document.getElementById('inImapUsername').value.trim(),
    imapPassword:document.getElementById('inImapPassword').value.trim(),
    useSsl:document.getElementById('inUseSsl').checked,
    companyEmail:document.getElementById('inCompanyEmail').value.trim(),
    bgvSenderFilter:document.getElementById('inBgvSenderFilter').value.trim(),
    replyEnabled:document.getElementById('inReplyEnabled').checked,
    replyFromName:document.getElementById('inReplyFromName').value.trim(),
    includePdfAttachment:document.getElementById('inIncludePdf').checked,
    includeVerificationLink:document.getElementById('inIncludeLink').checked
  };
  if(!data.imapHost||!data.imapUsername||!data.imapPassword||!data.companyEmail){
    toast('Fill in IMAP host, username, password, and company email','error');return;
  }
  var status=document.getElementById('inboundConfigStatus');
  status.textContent='Saving configuration...';
  status.className='upload-status';status.style.display='block';
  toast('Saving inbound email config...','info');
  fetch(API+'/bgv/inbound/config',{
    method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)
  })
  .then(function(r){return r.json();})
  .then(function(d){
    if(d.status==='ok'||d.status==='warning'){
      status.innerHTML='&#9989; Inbound email configured for '+data.companyEmail+' via '+data.imapHost;
      status.className='upload-status success';
      toast('Inbound email configured!','success');
    } else {
      status.textContent='&#10060; '+(d.message||'Failed to save config');
      status.className='upload-status error';
      toast('Failed to save config','error');
    }
  })
  .catch(function(e){
    status.innerHTML='&#10060; Error: '+e.message;
    status.className='upload-status error';
    toast('Error saving config','error');
  });
}

function checkInboundInbox(){
  var resultDiv=document.getElementById('inboxCheckResult');
  resultDiv.innerHTML='<span class="spinner"></span> Connecting to IMAP inbox and checking for BGV emails...';
  resultDiv.className='upload-status';resultDiv.style.display='block';
  toast('Checking inbox for BGV emails...','info');
  fetch(API+'/bgv/inbound/check',{method:'POST'})
  .then(function(r){return r.json();})
  .then(function(d){
    if(d.status==='error'){
      resultDiv.innerHTML='&#10060; Error:<br>'+(d.details&&d.details.length?d.details[0].error||d.details[0].warning||d.details[0].info||JSON.stringify(d.details[0]):'Unknown error');
      resultDiv.className='upload-status error';
      toast('Error checking inbox','error');
      return;
    }
    var html='';
    if(d.status==='warning'){
      html+='&#9888; Warning: '+(d.details&&d.details.length?d.details[0].warning||'':'')+'<br>';
    }
    html+='<div style="display:flex;gap:16px;flex-wrap:wrap;margin-top:8px;">';
    html+='<div style="background:#f0f7ff;padding:12px 20px;border-radius:8px;text-align:center;"><strong>'+d.totalEmails+'</strong><br><span style="font-size:12px;color:#666;">Total Emails</span></div>';
    html+='<div style="background:#f0fdf4;padding:12px 20px;border-radius:8px;text-align:center;"><strong>'+d.bgvMatched+'</strong><br><span style="font-size:12px;color:#666;">BGV Matched</span></div>';
    html+='<div style="background:#f0fdf4;padding:12px 20px;border-radius:8px;text-align:center;"><strong>'+d.repliesSent+'</strong><br><span style="font-size:12px;color:#059669;">Replies Sent</span></div>';
    html+='<div style="background:#fef2f2;padding:12px 20px;border-radius:8px;text-align:center;"><strong>'+d.failed+'</strong><br><span style="font-size:12px;color:#dc2626;">Failed</span></div>';
    html+='<div style="background:#fefce8;padding:12px 20px;border-radius:8px;text-align:center;"><strong>'+d.skipped+'</strong><br><span style="font-size:12px;color:#92400e;">Skipped</span></div>';
    html+='</div>';
    if(d.details&&d.details.length>1){
      html+='<div style="margin-top:12px;font-size:12px;color:#555;max-height:200px;overflow-y:auto;">';
      for(var i=1;i<d.details.length;i++){
        var item=d.details[i];
        var icon=item.action==='replied'?'&#9989;':item.action==='skipped'?'&#9233;':'&#10060;';
        var color=item.action==='replied'?'#059669':item.action==='skipped'?'#92400e':'#dc2626';
        html+='<div style="padding:4px 0;color:'+color+';">'+icon+' '+item.action+': '+(item.email||'')+(item.sender?' from '+item.sender:'')+(item.error?' - '+item.error:'')+(item.verificationId?' [ID: '+item.verificationId+']':'')+'</div>';
      }
      html+='</div>';
    }
    if(d.totalEmails===0&&d.status==='ok'){
      html='<div style="color:#666;font-size:13px;">No emails found in the inbox for the specified period.</div>';
    }
    resultDiv.innerHTML=html;
    resultDiv.className='upload-status '+(d.status==='ok'?'success':'error');
    toast('Check complete: '+d.bgvMatched+' BGV emails found, '+d.repliesSent+' replies sent','success');
    refreshInboundLogs();
  })
  .catch(function(e){
    resultDiv.innerHTML='&#10060; Connection error: '+e.message+'. Is the server running?';
    resultDiv.className='upload-status error';
    toast('Error: '+e.message,'error');
  });
}

function refreshInboundLogs(){
  var tbody=document.getElementById('inboundLogBody');
  if(!tbody) return;
  tbody.innerHTML='<tr><td colspan="6" style="text-align:center;padding:30px;color:#999">Loading...</td></tr>';
  fetch(API+'/bgv/inbound/logs')
  .then(function(r){return r.json();})
  .then(function(d){
    if(!d.logs||d.logs.length===0){
      tbody.innerHTML='<tr><td colspan="6" style="text-align:center;padding:30px;color:#999">No inbound emails processed yet. Configure and check the inbox above.</td></tr>';
      return;
    }
    tbody.innerHTML='';
    d.logs.forEach(function(log){
      var statusColor=log.bgvStatus==='processed'?'#059669':log.bgvStatus==='failed'?'#dc2626':log.bgvStatus==='skipped'?'#92400e':'#f59e0b';
      var statusIcon=log.bgvStatus==='processed'?'&#9989;':log.bgvStatus==='failed'?'&#10060;':log.bgvStatus==='skipped'?'&#9233;':'&#9201;';
      var replyStatus=log.replySent?'<span style="color:#059669;font-weight:600;">&#9989; Sent</span>':'<span style="color:#999;">-</span>';
      var kwHtml=log.detectedKeywords&&log.detectedKeywords.length
        ? '<span style="font-size:11px;color:#666;">'+log.detectedKeywords.slice(0,3).join(', ')+(log.detectedKeywords.length>3?'...':'')+'</span>'
        : '<span style="font-size:11px;color:#999;">-</span>';
      var tr=document.createElement('tr');
      tr.innerHTML=
        '<td style="font-size:11px;white-space:nowrap;">'+(log.processedAt||'')+'</td>'+
        '<td style="font-size:12px;">'+log.sender+'</td>'+
        '<td style="font-size:12px;max-width:250px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" title="'+escapeHtmlAttr(log.subject)+'">'+log.subject+'</td>'+
        '<td>'+kwHtml+'</td>'+
        '<td><span style="color:'+statusColor+';font-weight:600;">'+statusIcon+' '+log.bgvStatus+'</span></td>'+
        '<td>'+replyStatus+(log.replyVerificationId?'<br><code style="font-size:10px;">'+log.replyVerificationId+'</code>':'')+'</td>';
      tbody.appendChild(tr);
    });
  })
  .catch(function(e){
    tbody.innerHTML='<tr><td colspan="6" style="text-align:center;padding:30px;color:#dc2626">Error: '+e.message+'</td></tr>';
  });
}

function loadInboundConfig(){
  fetch(API+'/bgv/inbound/config')
  .then(function(r){return r.json();})
  .then(function(d){
    if(d.configured){
      var status=document.getElementById('inboundConfigStatus');
      if(status){
        status.innerHTML='&#9989; Inbound email configured: '+d.companyEmail+' via '+d.imapHost+':'+d.imapPort;
        status.className='upload-status success';status.style.display='block';
      }
      if(d.imapHost) document.getElementById('inImapHost').value=d.imapHost;
      if(d.imapPort) document.getElementById('inImapPort').value=d.imapPort;
      if(d.imapUsername) document.getElementById('inImapUsername').value=d.imapUsername;
      if(d.companyEmail) document.getElementById('inCompanyEmail').value=d.companyEmail;
      if(d.bgvSenderFilter) document.getElementById('inBgvSenderFilter').value=d.bgvSenderFilter;
      if(d.replyFromName) document.getElementById('inReplyFromName').value=d.replyFromName;
      document.getElementById('inReplyEnabled').checked=d.replyEnabled!==false;
      document.getElementById('inIncludePdf').checked=d.includePdfAttachment!==false;
      document.getElementById('inIncludeLink').checked=d.includeVerificationLink!==false;
    }
  }).catch(function(){});
}

// Initialize tabs on page load
document.addEventListener('DOMContentLoaded',function(){
  // Extend switchTab to load data for specific tabs
  var origSwitch=switchTab;
  window.switchTab=function(tabName){
    origSwitch(tabName);
    if(tabName==='bgv'){
      refreshBGVList();
    }
    if(tabName==='email-send'){
      loadEmailConfig();
      refreshAccessLog();
    }
  };

  // Extend switchBGVTab to load inbound data
  var _origSwitchBGVTab=window.switchBGVTab;
  window.switchBGVTab=function(tabName){
    if(typeof _origSwitchBGVTab==='function') _origSwitchBGVTab(tabName);
    if(tabName==='inbound'){
      loadInboundConfig();
      refreshInboundLogs();
    }
  };
});
