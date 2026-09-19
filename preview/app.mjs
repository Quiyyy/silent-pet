import { CELL,STATES,DIRECTIONS,SEQUENCES,duration,frameAt,directionCell,pointerDirection,sequenceAt } from './model.mjs';
const $=id=>document.getElementById(id);
const canvas=$('pet'),ctx=canvas.getContext('2d'),image=new Image();
let mode='state',state='idle',sequence='work',elapsed=0,direction=0,playing=true,speed=1,last=0,lastFilm='',lastFrame=-1,ready=false;
const stateButtons=new Map(),directionButtons=[];
function button(label,action,parent){const b=document.createElement('button');b.type='button';b.textContent=label;b.addEventListener('click',action);parent.append(b);return b;}
for(const [key,value] of Object.entries(STATES))stateButtons.set(key,button(value.label,()=>selectState(key),$('states')));
DIRECTIONS.forEach((deg,i)=>directionButtons.push(button(deg+'°',()=>{mode='direction';direction=i;playing=false;elapsed=0;paint();},$('directions'))));
for(const [key,value] of Object.entries(SEQUENCES))button(value.label,()=>{mode='sequence';sequence=key;elapsed=0;playing=true;paint();},$('sequences'));
function selectState(key){mode='state';state=key;elapsed=0;playing=true;paint();}
function active(){
  if(mode==='sequence'){const s=sequenceAt(sequence,elapsed);return {state:s.state,frame:frameAt(s.state,s.elapsed),row:STATES[s.state].row,column:frameAt(s.state,s.elapsed)};}
  if(mode==='neutral'||(mode==='pointer'&&direction===null))return {state:'neutral',frame:0,row:0,column:6};
  if(['direction','look-loop','pointer'].includes(mode)){const i=mode==='look-loop'?Math.floor(elapsed/160)%16:direction;return {state:'look',frame:i,...directionCell(i)};}
  const frame=frameAt(state,elapsed);return {state,frame,row:STATES[state].row,column:frame};
}
function draw(target,row,column){target.clearRect(0,0,CELL.width,CELL.height);if(ready)target.drawImage(image,column*CELL.width,row*CELL.height,CELL.width,CELL.height,0,0,CELL.width,CELL.height);}
function filmstrip(a){
  const key=a.state;
  if(key!==lastFilm){lastFilm=key;$('filmstrip').replaceChildren();
    const count=key==='look'?16:key==='neutral'?1:STATES[key].durations.length;
    for(let i=0;i<count;i++){const b=document.createElement('button');b.type='button';b.setAttribute('aria-label',key==='look'?DIRECTIONS[i]+'度':'第'+(i+1)+'帧');const c=document.createElement('canvas');c.width=CELL.width;c.height=CELL.height;
      const cell=key==='look'?directionCell(i):{row:a.row,column:key==='neutral'?6:i};draw(c.getContext('2d'),cell.row,cell.column);b.append(c,document.createTextNode(key==='look'?DIRECTIONS[i]+'°':String(i+1)));b.addEventListener('click',()=>{playing=false;if(key==='look'){mode='direction';direction=i;}else if(key==='neutral')mode='neutral';else{mode='state';state=key;elapsed=STATES[key].durations.slice(0,i).reduce((x,y)=>x+y,0);}paint();});$('filmstrip').append(b);}
  }
  [...$('filmstrip').children].forEach((b,i)=>b.classList.toggle('active',i===a.frame));
}
function paint(){
  if(!ready)return;
  const a=active();draw(ctx,a.row,a.column);canvas.dataset.state=a.state;canvas.dataset.frame=String(a.frame);canvas.dataset.mode=mode;
  $('state-name').textContent=a.state==='look'?DIRECTIONS[a.frame]+'°':a.state==='neutral'?'默认姿势':STATES[a.state].label;
  $('mode-label').textContent=mode==='sequence'?SEQUENCES[sequence].label:mode==='pointer'?'预览区指针跟随':mode==='look-loop'?'16方向连续检查':['direction','neutral'].includes(mode)?'方向定位':'单个动作';
  $('play').textContent=playing?'暂停':'播放';$('play').setAttribute('aria-pressed',String(playing));
  $('frame-label').textContent=a.state==='look'?'方向 '+(a.frame+1)+' / 16':a.state==='neutral'?'默认姿势':'第 '+(a.frame+1)+' / '+STATES[a.state].durations.length+' 帧';
  for(const [k,b] of stateButtons)b.classList.toggle('active',a.state===k);
  directionButtons.forEach((b,i)=>b.classList.toggle('active',a.state==='look'&&a.frame===i));
  $('pointer').setAttribute('aria-pressed',String(mode==='pointer'));
  filmstrip(a);lastFrame=a.frame;
}
function step(delta){const a=active();playing=false;if(a.state==='look'){mode='direction';direction=(a.frame+delta+16)%16;}else if(a.state==='neutral'){mode='direction';direction=0;}else{mode='state';state=a.state;const n=STATES[state].durations.length,i=(a.frame+delta+n)%n;elapsed=STATES[state].durations.slice(0,i).reduce((x,y)=>x+y,0);}paint();}
$('play').addEventListener('click',()=>{if(mode==='direction'||mode==='neutral'||mode==='pointer'){mode='look-loop';elapsed=(direction??0)*160;}playing=!playing;paint();});
$('previous').addEventListener('click',()=>step(-1));$('next').addEventListener('click',()=>step(1));
$('neutral').addEventListener('click',()=>{mode='neutral';playing=false;paint();});
$('look-loop').addEventListener('click',()=>{mode='look-loop';elapsed=0;playing=true;paint();});
$('pointer').addEventListener('click',()=>{mode='pointer';direction=null;playing=false;paint();});
$('stage').addEventListener('pointermove',e=>{if(mode!=='pointer')return;const b=canvas.getBoundingClientRect();direction=pointerDirection(e.clientX-b.left-b.width/2,e.clientY-b.top-b.height/2);paint();});
$('stage').addEventListener('pointerleave',()=>{if(mode==='pointer'){direction=null;paint();}});
$('speed').addEventListener('change',()=>{speed=Number($('speed').value);});
$('background').addEventListener('change',()=>{$('stage').dataset.background=$('background').value;});
$('zoom').addEventListener('change',()=>{const z=Number($('zoom').value);canvas.style.width=CELL.width*z+'px';canvas.style.height=CELL.height*z+'px';document.querySelector('.baseline').style.top='calc(50% + '+98*z+'px)';document.querySelector('.scale-note').textContent=z===1?'192 × 208 · 实际宠物尺寸':z+'× · '+(z<1?'缩小检查':'放大检查');$('stage').style.height=Math.max(390,208*z+64)+'px';});
image.onload=()=>{if(image.naturalWidth!==1536||image.naturalHeight!==2288){$('asset-status').textContent='图集尺寸错误：需要1536×2288';return;}ready=true;$('asset-status').textContent='v2 图集已载入 · 9组动作 / 16方向'+(requested?' · 候选版本':'');paint();};
image.onerror=()=>{$('asset-status').textContent='图集未能读取，请从仓库根目录启动本地HTTP服务。';};
const requested=new URLSearchParams(location.search).get('atlas');
image.src=requested&&!requested.startsWith('/')&&/^[a-zA-Z0-9_./-]+$/.test(requested)?requested:'../spritesheet.webp';
function tick(now){if(last&&playing){elapsed+=Math.min(now-last,250)*speed;paint();}last=now;requestAnimationFrame(tick);}requestAnimationFrame(tick);
