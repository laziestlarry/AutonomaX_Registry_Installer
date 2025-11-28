
import {get} from './router.js';

export async function loadTeamCard(cfg){
  const res = await get(cfg.base_url, '/registryx/projects');
  const items = res.items || [];
  const sel = document.getElementById('team_project_sel');
  sel.innerHTML = '';
  items.forEach(p=>{
    const opt=document.createElement('option');
    opt.value=p.project_id; opt.textContent=p.name;
    sel.appendChild(opt);
  });
  document.getElementById('btn_team_load').addEventListener('click', ()=>renderTeam(cfg, sel.value));
  if(items.length){ await renderTeam(cfg, items[0].project_id); }
}

async function renderTeam(cfg, project_id){
  const box = document.getElementById('team_box');
  const data = await get(cfg.base_url, '/registryx/team?project_id='+encodeURIComponent(project_id));
  box.innerHTML = '';
  const tbl = document.createElement('table'); tbl.className='gridtbl';
  tbl.innerHTML = '<thead><tr><th>Role</th><th>Assignee</th><th>Capacity %</th><th>Work Packages</th><th>Notes</th></tr></thead>';
  const tb = document.createElement('tbody');
  (data.members||[]).forEach(m=>{
    const tr=document.createElement('tr');
    tr.innerHTML = `<td>${m.role||''}</td><td>${m.assignee||''}</td><td>${m.capacity_pct||''}</td><td>${m.work_packages||''}</td><td>${m.notes||''}</td>`;
    tb.appendChild(tr);
  });
  tbl.appendChild(tb);
  box.appendChild(tbl);
}
