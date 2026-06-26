const API = 'http://localhost:8080/api';
let txnCount = 0;

const SAMPLE_TXNS = [
  {date:'2026-01-02',description:'Salary Credit - ABC Corp',debit:'',credit:'45000.00'},
  {date:'2026-01-05',description:'Rent Payment',debit:'15000.00',credit:''},
  {date:'2026-01-10',description:'Electricity Bill',debit:'2340.00',credit:''},
  {date:'2026-01-15',description:'Online Shopping - Amazon',debit:'5678.00',credit:''},
  {date:'2026-01-18',description:'Mobile Recharge',debit:'599.00',credit:''},
  {date:'2026-01-22',description:'Insurance Premium',debit:'8500.00',credit:''},
  {date:'2026-01-25',description:'Dividend Payment',debit:'',credit:'3200.00'},
  {date:'2026-01-28',description:'Grocery Store Purchase',debit:'3450.00',credit:''},
  {date:'2026-01-30',description:'Interest Credited',debit:'',credit:'187.50'}
];

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
  loadSampleData();
  setupUpload();
  var hash=window.location.hash.replace('#','');
  if(hash) setTimeout(function(){switchTab(hash);},100);
  window.addEventListener('hashchange',function(){
    var h=window.location.hash.replace('#','');
    if(h) switchTab(h);
  });
});

function loadSampleData(){
  document.getElementById('bankName').value='HDFC Bank';
  document.getElementById('period').value='January 2026';
  document.getElementById('accountHolder').value='Rahul Sharma';
  document.getElementById('accountNumber').value='1234567890';
  document.getElementById('branch').value='Koramangala Branch';
  document.getElementById('ifsc').value='HDFC0001234';
  document.getElementById('address').value='123, MG Road, Bangalore - 560001';
  document.getElementById('openingBalance').value='25000.00';
  SAMPLE_TXNS.forEach(t=>addTransaction(t.date,t.description,t.debit,t.credit));
  updateSummary();
}

function addTransaction(date,desc,debit,credit){
  txnCount++;
  const tr=document.createElement('tr');tr.id='txn-'+txnCount;
  tr.innerHTML='<td><input type="text" class="txn-date" value="'+(date||'')+'" placeholder="2026-01-01"></td>'+
    '<td><input type="text" class="txn-desc" value="'+(desc||'')+'" placeholder="Description"></td>'+
    '<td><input type="text" class="txn-debit" value="'+(debit||'')+'" placeholder="0.00" oninput="updateSummary()"></td>'+
    '<td><input type="text" class="txn-credit" value="'+(credit||'')+'" placeholder="0.00" oninput="updateSummary()"></td>'+
    '<td><button class="btn-icon" onclick="removeTransaction(\''+tr.id+'\')">&#10005;</button></td>';
  document.getElementById('txnBody').appendChild(tr);
  updateSummary();
}

function removeTransaction(id){
  var el=document.getElementById(id);if(el){el.remove();updateSummary();}
}

function updateSummary(){
  var td=0,tc=0;
  document.querySelectorAll('#txnBody tr').forEach(function(tr){
    td+=parseFloat(tr.querySelector('.txn-debit').value)||0;
    tc+=parseFloat(tr.querySelector('.txn-credit').value)||0;
  });
  var op=parseFloat(document.getElementById('openingBalance').value)||0;
  document.getElementById('totalDebits').value=td.toFixed(2);
  document.getElementById('totalCredits').value=tc.toFixed(2);
  document.getElementById('closingBalance').value=(op-td+tc).toFixed(2);
}

function collectFormData(){
  var txns=[];
  document.querySelectorAll('#txnBody tr').forEach(function(tr){
    txns.push({date:tr.querySelector('.txn-date').value,description:tr.querySelector('.txn-desc').value,
      debit:tr.querySelector('.txn-debit').value||'',credit:tr.querySelector('.txn-credit').value||''});
  });
  return {
    bankName:document.getElementById('bankName').value,period:document.getElementById('period').value,
    accountHolder:document.getElementById('accountHolder').value,accountNumber:document.getElementById('accountNumber').value,
    branch:document.getElementById('branch').value,ifsc:document.getElementById('ifsc').value,
    address:document.getElementById('address').value,openingBalance:document.getElementById('openingBalance').value,
    totalDebits:document.getElementById('totalDebits').value,totalCredits:document.getElementById('totalCredits').value,
    closingBalance:document.getElementById('closingBalance').value,transactions:txns
  };
}

function downloadPlain(){ downloadPdf('/generate-plain','statement-plain.pdf'); }
function downloadEncrypted(){
  var an=document.getElementById('accountNumber').value;
  downloadPdf('/generate','statement-encrypted.pdf');
  toast('Password: '+an.slice(-4)+' (last 4 digits)','info');
}

function downloadPdf(endpoint,filename){
  var data=collectFormData();
  if(!data.accountNumber){toast('Enter account number','error');return;}
  if(data.transactions.length===0){toast('Add at least one transaction','error');return;}
  toast('Generating PDF...','info');
  fetch(API+endpoint,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)})
  .then(function(r){if(!r.ok)throw new Error('Error: '+r.status);return r.blob();})
  .then(function(blob){
    var url=URL.createObjectURL(blob);
    var a=document.createElement('a');a.href=url;a.download=filename;
    document.body.appendChild(a);a.click();document.body.removeChild(a);
    URL.revokeObjectURL(url);toast('PDF downloaded!','success');
  }).catch(function(e){toast('Failed: '+e.message,'error');});
}

function resetForm(){
  if(!confirm('Reset all data?'))return;
  document.getElementById('txnBody').innerHTML='';txnCount=0;
  loadSampleData();toast('Reset to sample data','info');
}

// ========== UPLOAD ==========
function setupUpload(){
  var zone=document.getElementById('uploadZone');
  var input=document.getElementById('fileInput');
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
  document.getElementById('fileInput').files[0]?null:null;
  // Store file reference
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
      status.textContent='Uploaded successfully! Password: '+accountId.slice(-4);
      status.className='upload-status success';clearFile();refreshList();
      toast('PDF uploaded for account '+accountId,'success');
    } else { status.textContent='Error: '+d.message;status.className='upload-status error'; }
  })
  .catch(function(e){status.textContent='Error: '+e.message;status.className='upload-status error';});
}

function refreshList(){
  var tbody=document.getElementById('uploadListBody');
  tbody.innerHTML='<tr><td colspan="4" style="text-align:center;padding:30px;color:#999">Loading...</td></tr>';
  fetch(API+'/list').then(function(r){return r.json();}).then(function(data){
    if(data.length===0){
      tbody.innerHTML='<tr><td colspan="4" style="text-align:center;padding:30px;color:#999">No uploads yet. Upload a PDF or generate a statement.</td></tr>';
    } else {
      tbody.innerHTML='';
      data.forEach(function(item){
        var pw=item.accountId.length>=4?item.accountId.slice(-4):item.accountId;
        var tr=document.createElement('tr');
        tr.innerHTML='<td><strong>'+item.accountId+'</strong></td>'+
          '<td>'+item.file+'</td><td><code>'+pw+'</code></td>'+
          '<td><a href="'+API+'/replace?accountId='+item.accountId+'" target="_blank" class="btn btn-sm btn-outline" style="text-decoration:none">Test Replace</a></td>';
        tbody.appendChild(tr);
      });
    }
    document.getElementById('uploadCount').textContent=data.length+' file(s)';
  }).catch(function(e){tbody.innerHTML='<tr><td colspan="4" style="text-align:center;padding:30px;color:#dc2626">Error loading: '+e.message+'</td></tr>';});
}

function toast(msg,type){
  var t=document.getElementById('toast');t.textContent=msg;
  t.className='toast '+type+' show';
  clearTimeout(t._h);t._h=setTimeout(function(){t.classList.remove('show');},4000);
}
