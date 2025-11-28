
# Panel Wiring — Indexer + Team Card

Add these cards where you render other portfolio UI (after including `router.js`):

```html
<!-- Team Assignments -->
<div class="card">
  <h2>Team Assignments</h2>
  <div class="small">Pick a project to view roles/work packages</div>
  <select id="team_project_sel"></select>
  <button id="btn_team_load">Load Team</button>
  <div id="team_box"></div>
</div>

<!-- Search / Index -->
<div class="card">
  <h2>Registry Index</h2>
  <div class="small">Local keyword search across mission/strategies/goals/tasks/actions/steps</div>
  <div>Index size: <span id="index_count">0</span> | <button id="btn_build_index">Build/Refresh</button></div>
  <div style="margin-top:6px">
    <input id="index_query" placeholder="Search text or project name" style="width:60%"/>
    <button id="btn_index_search">Search</button>
  </div>
  <div id="index_results"></div>
</div>

<script type="module">
  import {loadTeamCard} from './assets/team.js';
  import {loadSearchCard} from './assets/search_index.js';
  const cfg = await (await fetch('./data/endpoints.json')).json();
  await loadTeamCard(cfg);
  await loadSearchCard(cfg);
</script>
```

> Needs CSVs under `DATA_DIR/registry/`: `Project_Registry.csv`, `Team_Assignments.csv`.
> Use `/registryx/index/build` to generate `index.json` server-side for fast panel loads.
