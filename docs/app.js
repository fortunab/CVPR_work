'use strict';
const $ = s => document.querySelector(s);
const $$ = s => [...document.querySelectorAll(s)];
const names = {cbmp:'CBMP',multi_prototype_unbalanced:'Unbalanced multi-prototype',linear_logistic:'Linear logistic',trainable_cosine:'Trained cosine',linear_group_center_weighted:'Weighted linear',cosine_group_center_weighted:'Weighted cosine',single_centroid_group_weighted:'Group-weighted centroid',single_centroid_center_balanced:'Center-balanced centroid',single_centroid_image_weighted:'Image-weighted centroid',K1_beta0:'K = 1 · β = 0',K1_beta1:'K = 1 · β = 1',K4_beta0:'K = 4 · β = 0',K4_beta1:'K = 4 · β = 1'};
let resultData, visibleRecords=[];
function label(m){return names[m]||m;}
function options(el,values,selected){el.replaceChildren(...values.map(([value,text])=>{const o=document.createElement('option');o.value=value;o.textContent=text;return o}));if(values.some(v=>v[0]===selected))el.value=selected;}
function initFilters(){const hist=$('#dataset').value==='camelyon';options($('#encoder'),(hist?['ResNet18','UNI','CONCH']:['ResNet18','DINOv2']).map(x=>[x,x]),hist?'UNI':'ResNet18');options($('#target'),hist?[['2','H2 · primary'],['1','H1 · secondary']]:['C2','C4','C5','C6'].map(x=>[x,x]),hist?'2':'C5');}
function renderResults(){if(!resultData)return;const dataset=$('#dataset').value,encoder=$('#encoder').value,protocol=$('#protocol').value,target=$('#target').value,metric=$('#metric').value;const meta=resultData.metrics[metric],factor=meta.display==='percent'?100:1,digits=factor===100?2:4;
 const records=resultData.records.filter(r=>r.dataset===dataset&&r.encoder===encoder&&r.protocol===protocol&&String(r.center)===target).sort((a,b)=>meta.higherIsBetter?b[metric]-a[metric]:a[metric]-b[metric]);visibleRecords=records;
 $('#bars').replaceChildren();$('#result-rows').replaceChildren();if(!records.length){$('#bars').textContent='No recorded comparison matches these settings.';return;}
 const maximum=factor===100?100:Math.max(...records.map(r=>r[metric]))*1.05;
 for(const r of records){const value=r[metric]*factor;const row=document.createElement('div');row.className='chart-row'+((r.method==='cbmp'||r.method.startsWith('K'))?' featured':'');const n=document.createElement('span');n.className='bar-label';n.textContent=label(r.method);const track=document.createElement('div');track.className='bar-track';track.setAttribute('aria-hidden','true');const fill=document.createElement('div');fill.className='bar-fill';fill.style.width=Math.max(0,Math.min(100,value/maximum*100))+'%';track.append(fill);const v=document.createElement('span');v.className='bar-value';v.textContent=value.toFixed(digits);row.append(n,track,v);$('#bars').append(row);
 const tr=document.createElement('tr');[label(r.method),value.toFixed(digits),(r[metric+'_seed_sd']*factor).toFixed(digits),String(r.fitting_seeds)].forEach(x=>{const td=document.createElement('td');td.textContent=x;tr.append(td)});$('#result-rows').append(tr);}
 const p=resultData.protocols.find(p=>p.id===protocol);$('#result-tag').textContent=p.label;$('#result-context').textContent=`${encoder} · ${dataset==='camelyon'?'H'+target+(target==='2'?' primary':' secondary'):target} · 10 fitting seeds`;
 $('#chart-title').textContent=(dataset==='camelyon'?'Patch ':'Frame ')+meta.label.toLowerCase()+(factor===100?' (%)':'');$('#metric-direction').textContent=meta.higherIsBetter?'Higher is better ↑':'Lower is better ↓';$('#protocol-note').textContent=p.description;
 const best=records[0];$('#result-best').textContent=(best[metric]*factor).toFixed(digits)+(factor===100?'%':'');$('#result-best-label').textContent=label(best.method)+' · leading point estimate';
 const cbmp=records.find(r=>r.method==='cbmp');if(cbmp){const delta=(cbmp[metric]-best[metric])*factor;$('#result-delta').textContent=best.method==='cbmp'?'CBMP has the leading point estimate for this setting. This result is specific to the selected cohort, representation and protocol.':`CBMP: ${(cbmp[metric]*factor).toFixed(digits)}${factor===100?'%':''}. Its point estimate differs from ${label(best.method).toLowerCase()} by ${delta>=0?'+':''}${delta.toFixed(digits)}${factor===100?' percentage points':''}.`;}else{$('#result-delta').textContent='Fixed prototype settings isolate prototype count K and center balance β. These settings are not selected using target performance.';}
}
$('#dataset').addEventListener('change',()=>{initFilters();renderResults()});['encoder','protocol','target','metric'].forEach(id=>$('#'+id).addEventListener('change',renderResults));
try{resultData=JSON.parse($('#recorded-results').textContent);initFilters();renderResults()}catch{$('#bars').textContent='The interactive metrics could not be loaded. Download the CSV summaries below to inspect the results.';$('#result-context').textContent='Recorded CSV downloads remain available.';}
function toast(s){$('#toast').textContent=s;$('#toast').classList.add('visible');setTimeout(()=>$('#toast').classList.remove('visible'),2400)}
function downloadText(name,text,type='text/plain'){const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([text],{type}));a.download=name;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(a.href),1000)}
$('#download-results').addEventListener('click',()=>{if(!visibleRecords.length)return;if(window.CBMP_ANONYMOUS_FILE_BASE){window.location.assign(window.CBMP_ANONYMOUS_FILE_BASE+'downloads/'+($('#dataset').value==='camelyon'?'histology_image_metrics.csv':'original_image_metrics.csv'));return;}const metric=$('#metric').value;const header=['task','protocol','center','method','fitting_seeds',metric,metric+'_seed_sd'];downloadText('cbmp-comparison.csv',header.join(',')+'\n'+visibleRecords.map(r=>header.map(k=>r[k]).join(',')).join('\n')+'\n','text/csv')});
if(window.CBMP_ANONYMOUS_FILE_BASE)$('#download-results').textContent='Open the source CSV ↗';
$$('[data-rank]').forEach(button=>button.addEventListener('click',()=>{const values=button.dataset.rank==='cbmp'?[94.86,55.33,57.90]:[94.13,81.10,81.95];$$('[data-rank]').forEach(b=>{b.classList.toggle('active',b===button);b.setAttribute('aria-pressed',String(b===button))});$('#rank-same').innerHTML=values[0].toFixed(2)+'<span>%</span>';$('#rank-across').innerHTML=values[1].toFixed(2)+'<span>%</span>';$('#rank-pooled').textContent=values[2].toFixed(2)+'%';$('#rank-same-bar').style.width=values[0]+'%';$('#rank-across-bar').style.width=values[1]+'%';}));
const svgNS='http://www.w3.org/2000/svg';let seed=33;function random(){seed=(seed*16807)%2147483647;return(seed-1)/2147483646}for(let i=0;i<92;i++){const first=i<46,c=document.createElementNS(svgNS,'circle');const a=random()*Math.PI*2,rad=Math.sqrt(random());c.setAttribute('cx',((first?150:323)+Math.cos(a)*rad*(first?80:76)).toFixed(1));c.setAttribute('cy',((first?140:226)+Math.sin(a)*rad*67).toFixed(1));c.setAttribute('r',(2.3+random()*2).toFixed(1));c.setAttribute('fill',first?'#7c9e7f':'#bf735f');c.setAttribute('opacity',(.45+random()*.4).toFixed(2));$('#embedding-points').append(c)}
let guideData;let shell='powershell',environment='venv',stage='setup';const stageNames={setup:'setup · Python 3.11',check:'installation checks',run:'classifier refit & comparison'};
function renderCode(){if(!guideData)return;$('#terminal-title').textContent=`${shell==='bash'?'Bash / Linux':'PowerShell'} / ${environment} · ${stageNames[stage]}`;$('#repro-code').textContent=guideData.routes[shell][environment][stage];$('#repro-hint').textContent=guideData.hints[stage];}
try{guideData=JSON.parse($('#recorded-guide').textContent);renderCode()}catch{$('#repro-code').textContent='Open the complete walkthrough or download the Markdown guide below.';}
$$('.repro-routes button').forEach(button=>button.addEventListener('click',()=>{shell=button.dataset.shell;environment=button.dataset.env;$$('.repro-routes button').forEach(b=>{b.classList.toggle('active',b===button);b.setAttribute('aria-pressed',String(b===button))});renderCode()}));
$$('.repro-steps button').forEach(button=>button.addEventListener('click',()=>{stage=button.dataset.stage;$$('.repro-steps button').forEach(b=>b.classList.toggle('active',b===button));renderCode()}));
$('#copy-code').addEventListener('click',async()=>{const text=$('#repro-code').textContent;try{await navigator.clipboard.writeText(text);toast('Commands copied')}catch{const selection=window.getSelection(),range=document.createRange();range.selectNodeContents($('#repro-code'));selection.removeAllRanges();selection.addRange(range);toast('Select and copy the commands with your keyboard')}});

// Inspect the SVG without rasterizing or changing the recorded results.
const figureButton = $('.figure-zoom');
const figureDialog = $('#figure-dialog');
figureButton.addEventListener('pointermove', event => {
  if (event.pointerType === 'touch') return;
  const bounds = $('.figure-viewport').getBoundingClientRect();
  figureButton.style.setProperty('--zoom-x', `${Math.max(0, Math.min(100, (event.clientX - bounds.left) / bounds.width * 100))}%`);
  figureButton.style.setProperty('--zoom-y', `${Math.max(0, Math.min(100, (event.clientY - bounds.top) / bounds.height * 100))}%`);
});
figureButton.addEventListener('pointerleave', () => {
  figureButton.style.removeProperty('--zoom-x');
  figureButton.style.removeProperty('--zoom-y');
});
figureButton.addEventListener('click', () => {
  const enlarged = $('#embedding').cloneNode(true);
  // Keep SVG resource IDs unique when the original and enlarged views coexist.
  enlarged.removeAttribute('id');
  enlarged.querySelectorAll('[id]').forEach(node => {
    if (node.id === 'grid') node.id = 'enlarged-grid';
    else node.removeAttribute('id');
  });
  enlarged.querySelector('[fill="url(#grid)"]').setAttribute('fill', 'url(#enlarged-grid)');
  $('#enlarged-embedding').replaceChildren(enlarged);
  closeStatTips();
  setContentsOpen(false);
  figureDialog.showModal();
  document.body.classList.add('figure-open');
});
$('.dialog-close').addEventListener('click', () => figureDialog.close());
figureDialog.addEventListener('click', event => {
  if (event.target !== figureDialog) return;
  const bounds = figureDialog.getBoundingClientRect();
  if (event.clientX < bounds.left || event.clientX > bounds.right || event.clientY < bounds.top || event.clientY > bounds.bottom) figureDialog.close();
});
figureDialog.addEventListener('close', () => {
  document.body.classList.remove('figure-open');
  figureButton.focus({preventScroll:true});
});

// One explanation at a time; hover, focus and touch share the same state.
const statItems = $$('.stat-item');
function closeStatTips(except) {
  statItems.forEach(item => {
    if (item === except) return;
    item.classList.remove('is-open');
    item.querySelector('.stat-info').setAttribute('aria-expanded', 'false');
    delete item.dataset.pinned;
  });
}
function openStatTip(item) {
  closeStatTips(item);
  item.classList.add('is-open');
  item.querySelector('.stat-info').setAttribute('aria-expanded', 'true');
}
statItems.forEach(item => {
  const button = item.querySelector('.stat-info');
  item.addEventListener('pointerenter', event => { if (event.pointerType !== 'touch') openStatTip(item); });
  item.addEventListener('pointerleave', () => { if (!item.dataset.pinned && !item.contains(document.activeElement)) closeStatTips(); });
  button.addEventListener('focus', () => openStatTip(item));
  button.addEventListener('click', () => {
    if (item.dataset.pinned) closeStatTips();
    else { openStatTip(item); item.dataset.pinned = 'true'; }
  });
  item.addEventListener('focusout', event => {
    if (!item.contains(event.relatedTarget)) closeStatTips();
  });
});
document.addEventListener('click', event => {
  if (!event.target.closest('.stat-item')) closeStatTips();
  if (!event.target.closest('.section-menu')) setContentsOpen(false);
});
document.addEventListener('keydown', event => {
  if (event.key !== 'Escape') return;
  closeStatTips();
  if ($('.section-menu').classList.contains('is-open')) {
    setContentsOpen(false);
    $('.contents-toggle').focus();
  }
});

const contents = $('.section-menu');
const contentsToggle = $('.contents-toggle');
function setContentsOpen(open) {
  contents.classList.toggle('is-open', open);
  contentsToggle.setAttribute('aria-expanded', String(open));
  contentsToggle.querySelector('span').textContent = open ? '−' : '+';
}
contentsToggle.addEventListener('click', () => setContentsOpen(!contents.classList.contains('is-open')));
const sectionLinks = $$('#section-links a');
const sections = sectionLinks.map(link => $(link.getAttribute('href')));
sectionLinks.forEach(link => link.addEventListener('click', () => {
  setContentsOpen(false);
  // Preserve native fragment navigation and move keyboard focus to its destination.
  const section = $(link.getAttribute('href'));
  section.setAttribute('tabindex', '-1');
  section.focus({preventScroll:true});
}));
let scrollScheduled = false;
function updateCurrentSection() {
  scrollScheduled = false;
  let current = sections[0];
  const offset = $('.site-header').getBoundingClientRect().height + 36;
  sections.forEach(section => { if (section.getBoundingClientRect().top <= offset) current = section; });
  if (window.scrollY + window.innerHeight >= document.documentElement.scrollHeight - 8) current = sections[sections.length - 1];
  sectionLinks.forEach(link => {
    if (link.getAttribute('href') === '#' + current.id) link.setAttribute('aria-current', 'location');
    else link.removeAttribute('aria-current');
  });
}
function scheduleSectionUpdate() {
  if (scrollScheduled) return;
  scrollScheduled = true;
  window.requestAnimationFrame(updateCurrentSection);
}
window.addEventListener('scroll', scheduleSectionUpdate, {passive:true});
window.addEventListener('resize', () => { setContentsOpen(false); scheduleSectionUpdate(); });
updateCurrentSection();

