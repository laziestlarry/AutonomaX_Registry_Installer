
import {get} from './router.js';

export async function loadSearchCard(cfg){
  const trigger = document.getElementById('btn_build_index');
  trigger.addEventListener('click', async ()=>{
    await get(cfg.base_url, '/registryx/index/build');
    await refreshIndex(cfg);
  });
  await refreshIndex(cfg);
}

async function refreshIndex(cfg){
  const data = await get(cfg.base_url, '/registryx/index');
  window._idx = data.items || [];
  document.getElementById('index_count').textContent = data.count||0;

  const q = document.getElementById('index_query');
  const btn = document.getElementById('btn_index_search');
  btn.addEventListener('click', ()=>runSearch(q.value));
}

function runSearch(q){
  const root = document.getElementById('index_results');
  root.innerHTML = '';
  if(!q){ return; }
  const needle = q.toLowerCase();
  const hits = (window._idx||[]).filter(d => (d.text||'').toLowerCase().includes(needle) || (d.name||'').toLowerCase().includes(needle));
  hits.slice(0,200).forEach(h=>{
    const card=document.createElement('div'); card.className='card';
    const meta = `${h.family||''} • ${h.channel||''} • ${h.status||''} • ${h.percent_complete||''}%`;
    card.innerHTML = `<h4>${h.name}</h4><div class='small'>${meta}</div><pre>${(h.text||'').slice(0,800)}</pre>`;
    root.appendChild(card);
  });
}
