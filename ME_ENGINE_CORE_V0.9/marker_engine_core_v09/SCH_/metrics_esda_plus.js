/* metrics_esda_plus.js – generisch, keine Namen */
export function makeESDA(schema){
  const sets = schema.metrics?.sets || {E:[], D:[]};
  const k = schema.metrics?.windows?.cri_k ?? 3;
  const jsdTau = schema.metrics?.windows?.episode_jsd_threshold ?? 0.15;
  const driftWin = schema.metrics?.windows?.drift_window_messages ?? 30;
  const primaryOrder = schema.metrics?.primaryOrder || ["Emotion","Misstrauen","Defensive","Transparenz","Deeskalation","Themenwechsel","Grenzsetzung"];
  const tr = schema.metrics?.transitionRules || {escalating:[], deescalating:[]};

  const isE = (A)=> sets.E.some(id => A[id]);
  const isD = (A)=> sets.D.some(id => A[id]);

  function primaryState(A){
    // Map Atomics -> States (passe ggf. auf deine Mapping-Funktion an)
    const s = {
      Emotion: A.ATO_ANGER,
      Misstrauen: A.ATO_TRUST_DEFICIT_STATEMENT,
      Defensive: A.ATO_DEFENSIVE_REBUTTAL,
      Transparenz: A.ATO_REQUEST_TRANSPARENCY,
      Deeskalation: (A.ATO_DEESCALATION_OFFER || A.ATO_APOLOGY_DE),
      Themenwechsel: A.ATO_TOPIC_SWITCH_TECH,
      Grenzsetzung: A.ATO_BOUNDARY_SET
    };
    for(const label of primaryOrder){ if(s[label]) return label; }
    return null;
  }

  function uniqSenders(messages){
    const ids=[...new Set(messages.map(m=>m.sender))].sort();
    const map = new Map(ids.map((id,i)=>[id, `party_${i+1}`]));
    return {ids, map};
  }

  function transitions(messages){
    const edges = new Map(); // key "A->B" -> count
    for(let i=0;i<messages.length-1;i++){
      const a=messages[i], b=messages[i+1];
      if(a.sender===b.sender) continue;
      const A=primaryState(a.A), B=primaryState(b.A);
      if(!A || !B || A===B) continue;
      const key = `${A}->${B}`;
      edges.set(key,(edges.get(key)||0)+1);
    }
    return [...edges].map(([k,count])=>{ const [from,to]=k.split("->"); return {from,to,count}; });
  }

  function CRI(messages){
    let Ecount=0, repaired=0;
    for(let i=0;i<messages.length;i++){
      const m=messages[i];
      if(!isE(m.A)) continue;
      Ecount++;
      const s0=m.sender;
      let resp=0, ok=false;
      for(let j=i+1;j<messages.length && resp<k; j++){
        if(messages[j].sender===s0) continue;
        resp++;
        if(isD(messages[j].A)){ ok=true; break; }
      }
      if(ok) repaired++;
    }
    return {k, E: Ecount, repaired, cri: Ecount? (repaired/Ecount) : 0};
  }

  function resilience(messages){
    const bins=[0,1,2,3,4]; const counts=[0,0,0,0,0,0]; // last bin = 5+
    const delays=[];
    for(let i=0;i<messages.length;i++){
      const m=messages[i]; if(!isE(m.A)) continue;
      const s0=m.sender;
      let steps=0, found=false;
      for(let j=i+1;j<messages.length;j++){
        if(messages[j].sender===s0) continue;
        steps++;
        if(isD(messages[j].A)){ found=true; break; }
      }
      const bin = found ? Math.min(steps,5) : 5;
      counts[bin]++; if(found) delays.push(steps);
    }
    const med = median(delays);
    const p75 = percentile(delays, 0.75);
    return {bins:["0","1","2","3","4","5+"], counts, median: med, p75};
  }

  function median(arr){ if(!arr.length) return null; const s=[...arr].sort((a,b)=>a-b); const m=Math.floor(s.length/2); return s.length%2? s[m] : (s[m-1]+s[m])/2; }
  function percentile(arr, p){ if(!arr.length) return null; const s=[...arr].sort((a,b)=>a-b); const idx=Math.ceil(p*s.length)-1; return s[Math.max(0,idx)]; }

  function markerHistogram(messages, atoIds){
    const h = Object.fromEntries(atoIds.map(id=>[id,0]));
    let total=0;
    messages.forEach(m=>{
      atoIds.forEach(id=>{ if(m.A[id]){ h[id]++; total++; }});
    });
    // normalize to distribution (avoid zero-div by using eps on empty)
    const eps=1e-9; const norm=Object.fromEntries(atoIds.map(id=>[id, (h[id])/(total||eps)]));
    return {counts:h, dist:norm, total};
  }

  function jsd(P, Q){
    // P, Q: objects with same keys, sum to 1
    const keys=Object.keys(P); const M={};
    keys.forEach(k=> M[k]=(P[k]+Q[k])/2 );
    return 0.5*(kl(P,M)+kl(Q,M));
  }
  function kl(P,Q){ const keys=Object.keys(P); const eps=1e-12; let s=0;
    keys.forEach(k=>{ const p=Math.max(P[k],eps), q=Math.max(Q[k],eps); s += p*Math.log2(p/q); });
    return s;
  }

  function episodeCuts(messages, atoIds){
    if(messages.length<2) return [{from:0,to:messages.length-1, reason:"single"}];
    const slices=[]; let start=0;
    let prev = markerHistogram([messages[0]], atoIds).dist;
    for(let i=1;i<messages.length;i++){
      const curr = markerHistogram(messages.slice(start, i+1), atoIds).dist;
      const prevWindow = markerHistogram(messages.slice(Math.max(start,i-1), i), atoIds).dist; // small prev to compare
      const d = jsd(curr, prevWindow);
      const topChange = topMarker(messages.slice(Math.max(start,i-5), i), atoIds) !== topMarker(messages.slice(Math.max(start,i-4), i+1), atoIds);
      if(d>=jsdTau || topChange){
        slices.push({from:start, to:i-1, reason: d>=jsdTau? "jsd":"topchange", jsd:d});
        start=i;
      }
      prev = curr;
    }
    slices.push({from:start, to:messages.length-1, reason:"end"});
    return slices;
  }

  function topMarker(msgs, atoIds){
    const h = markerHistogram(msgs, atoIds).counts;
    const arr = Object.entries(h).sort((a,b)=>b[1]-a[1]);
    return arr[0]?.[0] || null;
  }

  function driftZ(messages, atoIds, win=driftWin){
    // per-msg vector of ATO counts (0/1) → rolling z per marker
    const series = {}; atoIds.forEach(id=>series[id]=[]);
    // cumulative sum for fast window
    const vals = atoIds.map(()=>[]);
    messages.forEach(m=>{
      atoIds.forEach((id,j)=>{ vals[j].push( m.A[id]?1:0 ); });
    });
    const eps=1e-9;
    atoIds.forEach((id,j)=>{
      const arr=vals[j];
      for(let t=0;t<arr.length;t++){
        const a=Math.max(0, t-win+1), b=t+1; const w=arr.slice(a,b);
        const mu=w.reduce((x,y)=>x+y,0)/(w.length||1);
        const sd=Math.sqrt(w.reduce((x,y)=>x+(y-mu)*(y-mu),0)/(w.length||1))||eps;
        series[id].push( (arr[t]-mu)/sd );
      }
    });
    return series; // id -> [z_t]
  }

  function initiativeStarts(episodes, messages){
    // returns count per sender for who starts an episode
    const c=new Map();
    episodes.forEach(ep=>{
      const s = messages[ep.from]?.sender;
      if(!s)
