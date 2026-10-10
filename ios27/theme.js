
/* PearisticOS 27 UI layer. No changes to the underlying app engine. */
(()=>{
 'use strict';
 const root=document.documentElement;
 root.dataset.pearEdition='27';
 const keyClarity='pear27-glass-clarity',keyReduce='pear27-reduce-transparency';
 const get=(name,fallback)=>{try{const val=localStorage.getItem(name);return val===null?fallback:JSON.parse(val)}catch{return fallback}};
 const set=(name,val)=>{try{localStorage.setItem(name,JSON.stringify(val))}catch{}};
 let clarity=Math.max(0,Math.min(100,Number(get(keyClarity,65))||0));
 let reduce=!!get(keyReduce,false);
 function apply(){
   root.style.setProperty('--pear27-glass-alpha',(0.24+clarity*.006).toFixed(3));
   root.style.setProperty('--pear27-glass-blur',`${Math.round(10+clarity*.29)}px`);
   root.style.setProperty('--pear27-glass-sat',(1.15+clarity*.009).toFixed(2));
   root.classList.toggle('pear27-reduce-transparency',reduce);
 }
 apply();
 // Render Settings controls whenever the existing system rerenders Settings.
 function augmentSettings(){
  const appearance=document.querySelector('#appBody #appearance');
  if(!appearance || appearance.querySelector('.pear27-clarity-control'))return;
  const title=document.querySelector('#appBody>h2');
  if(title && !document.querySelector('#appBody .pear27-version-pill')){
    const label=document.createElement('span');label.className='pear27-version-pill';label.textContent='PEARISTICOS · iOS 27 STYLE';title.insertAdjacentElement('afterend',label);
  }
  const row=document.createElement('div');row.className='row';
  const copy=document.createElement('div');
  copy.innerHTML='<div class="row-label">Liquid Glass</div><div class="row-sub">Adjust the transparency of navigation and controls.</div>';
  const controls=document.createElement('label');controls.className='pear27-clarity-control';
  const slider=document.createElement('input');slider.type='range';slider.min='0';slider.max='100';slider.step='1';slider.value=clarity;slider.setAttribute('aria-label','Liquid Glass clarity');
  const output=document.createElement('output');output.value=clarity+'%';output.textContent=clarity+'%';
  controls.append(slider,output);row.append(copy,controls);appearance.append(row);
  slider.addEventListener('input',()=>{clarity=Number(slider.value);output.textContent=clarity+'%';output.value=clarity+'%';set(keyClarity,clarity);apply()});
  const reduceRow=document.createElement('div');reduceRow.className='row';
  const rCopy=document.createElement('div');rCopy.innerHTML='<div class="row-label">Reduce Transparency</div><div class="row-sub">Use solid backgrounds for clearer text or lower GPU load.</div>';
  const toggle=document.createElement('button');toggle.type='button';toggle.className='switch'+(reduce?' on':'');toggle.setAttribute('role','switch');toggle.setAttribute('aria-label','Reduce Transparency');toggle.setAttribute('aria-checked',reduce?'true':'false');
  toggle.addEventListener('click',()=>{reduce=!reduce;toggle.classList.toggle('on',reduce);toggle.setAttribute('aria-checked',String(reduce));set(keyReduce,reduce);apply()});
  reduceRow.append(rCopy,toggle);appearance.append(reduceRow);
  const system=document.querySelector('#appBody #systemSet');
  if(system&&!system.querySelector('#pear27Visit17')){
   const row=document.createElement('div');row.className='row';
   const label=document.createElement('div');label.innerHTML='<div class="row-label">iOS 17 edition</div><div class="row-sub">Open the preserved original PearisticOS design.</div>';
   const button=document.createElement('button');button.id='pear27Visit17';button.type='button';button.className='app-action secondary';button.textContent='Open iOS 17';
   button.addEventListener('click',()=>{location.href='https://asildorukatik.github.io/PearisticOS/'});
   row.append(label,button);system.append(row);
  }
 }
 let queued=false;
 const observer=new MutationObserver(()=>{if(!queued){queued=true;requestAnimationFrame(()=>{queued=false;augmentSettings()})}});
 observer.observe(document.querySelector('#appBody')||document.body,{childList:true,subtree:true});
 augmentSettings();
 // Dynamic subtle reflection, without changing the existing Dock geometry.
 const dock=document.getElementById('dock');
 if(dock){let raf=0,x=50;dock.addEventListener('pointermove',event=>{
   const r=dock.getBoundingClientRect();if(!r.width)return;x=Math.max(0,Math.min(100,(event.clientX-r.left)/r.width*100));
   if(raf)return;raf=requestAnimationFrame(()=>{dock.style.setProperty('--pear27-pointer-x',x+'%');raf=0})
 },{passive:true});dock.addEventListener('pointerleave',()=>dock.style.setProperty('--pear27-pointer-x','50%'),{passive:true})}
})();

