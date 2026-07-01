const $ = (id) => document.getElementById(id);
const esc = (v) => String(v ?? '').replace(/[&<>"]/g, s => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[s]));
function statusClass(ready, key){ if(ready) return 'ready'; if(key==='tiktok') return 'pending'; return ''; }
async function load(){
  const [status, overview, posts, revenue] = await Promise.all([
    fetch('/api/status').then(r=>r.json()),
    fetch('/api/overview').then(r=>r.json()),
    fetch('/api/posts?limit=25').then(r=>r.json()),
    fetch('/api/revenue').then(r=>r.json()),
  ]);
  $('generated').textContent = new Date(status.generated_at).toLocaleString();
  $('platforms').innerHTML = Object.entries(status.platforms).map(([key,p]) => `<article class="card ${statusClass(p.ready,key)}"><div class="status"><span class="dot"></span>${esc(key.toUpperCase())}</div><h3>${p.ready?'Ready':key==='tiktok'?'In review':'Not connected'}</h3><p>${esc(p.label)}${p.note?'<br><span class="muted">'+esc(p.note)+'</span>':''}</p></article>`).join('');
  const sc = overview.status_counts || {}; const pc = overview.platform_counts || {};
  $('overview').innerHTML = [
    ['Posted', sc.posted||0], ['Scheduled', sc.scheduled||0], ['Failed', sc.failed||0], ['Media', overview.media_count||0],
    ['YouTube jobs', pc.youtube||0], ['Facebook jobs', pc.facebook||0], ['Events', overview.event_count||0], ['Risks', (overview.risk_flags||[]).length],
  ].map(([label,num])=>`<div class="metric"><div class="num">${num}</div><div class="label">${label}</div></div>`).join('');
  $('revenue').innerHTML = `<b>Total tracked revenue:</b> ${revenue.total_revenue} ${revenue.currency}<br><b>Status:</b> ${esc(revenue.message)}<br><br>${Object.entries(revenue.source_status).map(([k,v])=>`<span class="tag">${esc(k)}: ${esc(v)}</span>`).join(' ')}`;
  const risks = overview.risk_flags || [];
  $('riskBadge').textContent = risks.length ? `${risks.length} blocked` : 'clear';
  $('riskBadge').className = risks.length ? 'pill risk-bad' : 'pill risk-ok';
  $('risks').innerHTML = risks.length ? risks.map(r=>`<p class="risk-bad"><b>Post ${r.post_id}</b> blocked terms: ${esc(r.matches.join(', '))}</p>`).join('') : '<p class="risk-ok"><b>Clear:</b> no internal metadata leaks detected in latest posts.</p><p class="muted">Run <code>hse media-audit</code> before every batch upload.</p>';
  $('posts').innerHTML = posts.posts.map(p => `<tr><td>${p.id}</td><td>${esc(p.platform)}</td><td><span class="tag ${esc(p.status)}">${esc(p.status)}</span></td><td>${esc(p.scheduled_at)}</td><td class="content">${esc(p.content)}</td><td>${p.release_url?`<a href="${esc(p.release_url)}">open</a>`:''}</td></tr>`).join('');
}
load().catch(err=>{document.body.innerHTML='<pre style="color:#fff;padding:24px">Dashboard failed: '+esc(err.stack||err)+'</pre>'});
