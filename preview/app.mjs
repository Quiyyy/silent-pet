import { CELL, STATES, DIRECTIONS, SEQUENCES, frameAt, directionCell, pointerDirection, sequenceAt } from './model.mjs';
import { PetInteraction, clampOffset } from './interaction.mjs';

const $ = id => document.getElementById(id);
const canvas = $('pet'), ctx = canvas.getContext('2d'), image = new Image(), stage = $('stage');
const motionPreference = matchMedia('(prefers-reduced-motion: reduce)');
const interaction = new PetInteraction({ reducedMotion: motionPreference.matches });
$('reduced-motion').checked = interaction.reducedMotion;
let mode = 'state', state = 'idle', sequence = 'work', elapsed = 0, direction = 0;
let playing = true, speed = 1, last = 0, lastFilm = '', ready = false;
let offset = { x: 0, y: 0 }, gesture = null;
const stateButtons = new Map(), directionButtons = [];
function button(label, action, parent) {
  const b = document.createElement('button');
  b.type = 'button'; b.textContent = label; b.addEventListener('click', action); parent.append(b); return b;
}
function positionPet() {
  offset = clampOffset(offset, stage.getBoundingClientRect(), canvas.getBoundingClientRect());
  canvas.style.transform = 'translate(' + offset.x + 'px,' + offset.y + 'px)';
  document.querySelector('.baseline').style.top = 'calc(50% + ' + (98 * Number($('zoom').value) + offset.y) + 'px)';
}
function releaseGesture() {
  const id = gesture?.id;
  gesture = null;
  if (id !== undefined && canvas.hasPointerCapture(id)) canvas.releasePointerCapture(id);
}
function cancelInteraction() {
  interaction.cancel(); releaseGesture();
}
function setMode(next) {
  if (mode === 'interactive' && next !== mode) {
    cancelInteraction(); offset = { x: 0, y: 0 }; positionPet();
  }
  mode = next;
  const interactive = mode === 'interactive';
  canvas.tabIndex = interactive ? 0 : -1;
  canvas.setAttribute('role', interactive ? 'button' : 'img');
  canvas.setAttribute('aria-label', interactive ? '猎豹，按回车或空格亲近，拖动可移动位置' : '宠物动作预览');
  stage.dataset.interactive = String(interactive);
  for (const id of ['play', 'previous', 'next', 'speed']) $(id).disabled = interactive;
  $('interaction-options').hidden = !interactive;
  $('interactive').setAttribute('aria-pressed', String(interactive));
  $('hint').textContent = interactive
    ? '靠近时注视；停留片刻或轻点，舒缓回应约 2.4 秒。拖动松手不会再触发亲近。'
    : '点击下方缩略帧可暂停定位。基线用于检查脚底与角色大小。';
}
for (const [key, value] of Object.entries(STATES)) stateButtons.set(key, button(value.label, () => selectState(key), $('states')));
DIRECTIONS.forEach((deg, i) => directionButtons.push(button(deg + '°', () => {
  setMode('direction'); direction = i; playing = false; elapsed = 0; paint();
}, $('directions'))));
for (const [key, value] of Object.entries(SEQUENCES)) button(value.label, () => {
  setMode('sequence'); sequence = key; elapsed = 0; playing = true; paint();
}, $('sequences'));
function selectState(key) { setMode('state'); state = key; elapsed = 0; playing = true; paint(); }
function active(now) {
  if (mode === 'interactive') {
    const s = interaction.snapshot(now);
    if (s.kind === 'gaze') return s.direction === null
      ? { ...s, state: 'neutral', frame: 0, row: 0, column: 6 }
      : { ...s, state: 'look', frame: s.direction, ...directionCell(s.direction) };
    return { ...s, row: STATES[s.state].row, column: s.frame };
  }
  if (mode === 'sequence') {
    const s = sequenceAt(sequence, elapsed), frame = frameAt(s.state, s.elapsed);
    return { state: s.state, frame, row: STATES[s.state].row, column: frame };
  }
  if (mode === 'neutral' || (mode === 'pointer' && direction === null)) return { state: 'neutral', frame: 0, row: 0, column: 6 };
  if (['direction', 'look-loop', 'pointer'].includes(mode)) {
    const i = mode === 'look-loop' ? Math.floor(elapsed / 160) % 16 : direction;
    return { state: 'look', frame: i, ...directionCell(i) };
  }
  const frame = frameAt(state, elapsed); return { state, frame, row: STATES[state].row, column: frame };
}
function draw(target, row, column) {
  target.clearRect(0, 0, CELL.width, CELL.height);
  if (ready) target.drawImage(image, column * CELL.width, row * CELL.height, CELL.width, CELL.height, 0, 0, CELL.width, CELL.height);
}
function filmstrip(a) {
  const key = a.state;
  if (key !== lastFilm) {
    lastFilm = key; $('filmstrip').replaceChildren();
    const count = key === 'look' ? 16 : key === 'neutral' ? 1 : STATES[key].durations.length;
    for (let i = 0; i < count; i++) {
      const b = document.createElement('button'), c = document.createElement('canvas');
      b.type = 'button'; b.setAttribute('aria-label', key === 'look' ? DIRECTIONS[i] + '度' : '第' + (i + 1) + '帧');
      c.width = CELL.width; c.height = CELL.height;
      const cell = key === 'look' ? directionCell(i) : { row: a.row, column: key === 'neutral' ? 6 : i };
      draw(c.getContext('2d'), cell.row, cell.column);
      b.append(c, document.createTextNode(key === 'look' ? DIRECTIONS[i] + '°' : String(i + 1)));
      b.addEventListener('click', () => {
        playing = false;
        if (key === 'look') { setMode('direction'); direction = i; }
        else if (key === 'neutral') setMode('neutral');
        else { setMode('state'); state = key; elapsed = STATES[key].durations.slice(0, i).reduce((x, y) => x + y, 0); }
        paint();
      });
      $('filmstrip').append(b);
    }
  }
  [...$('filmstrip').children].forEach((b, i) => b.classList.toggle('active', i === a.frame));
}
function paint(now = performance.now()) {
  if (!ready) return;
  const a = active(now);
  draw(ctx, a.row, a.column);
  canvas.dataset.state = a.state; canvas.dataset.frame = String(a.frame); canvas.dataset.mode = mode;
  canvas.dataset.kind = a.kind ?? 'inspection';
  canvas.dataset.reactionId = String(a.reactionId ?? 0);
  canvas.dataset.reactionSource = a.source ?? '';
  $('state-name').textContent = a.state === 'look' ? DIRECTIONS[a.frame] + '°' : a.state === 'neutral' ? '默认姿势' : STATES[a.state].label;
  $('mode-label').textContent = mode === 'interactive' ? '互动体验 · 浏览器原型'
    : mode === 'sequence' ? SEQUENCES[sequence].label : mode === 'pointer' ? '预览区指针跟随'
    : mode === 'look-loop' ? '16方向连续检查' : ['direction', 'neutral'].includes(mode) ? '方向定位' : '原生节奏检查';
  $('play').textContent = playing ? '暂停' : '播放'; $('play').setAttribute('aria-pressed', String(playing));
  $('frame-label').textContent = a.state === 'look' ? '方向 ' + (a.frame + 1) + ' / 16' : a.state === 'neutral' ? '默认姿势' : '第 ' + (a.frame + 1) + ' / ' + STATES[a.state].durations.length + ' 帧';
  for (const [k, b] of stateButtons) b.classList.toggle('active', a.state === k);
  directionButtons.forEach((b, i) => b.classList.toggle('active', a.state === 'look' && a.frame === i));
  $('pointer').setAttribute('aria-pressed', String(mode === 'pointer'));
  if (mode === 'interactive') {
    const labels = { drag: '跟着你移动', task: '专注当前任务', affection: '放松下来，轻轻回应', gaze: '注意到你了', idle: '安静陪伴' };
    const status = labels[a.kind] + (a.cooldownMs > 0 && a.kind !== 'affection' ? ' · 稍后再亲近' : '');
    if ($('interaction-status').textContent !== status) $('interaction-status').textContent = status;
  }
  filmstrip(a);
}
function step(delta) {
  const a = active(performance.now()); playing = false;
  if (a.state === 'look') { setMode('direction'); direction = (a.frame + delta + 16) % 16; }
  else if (a.state === 'neutral') { setMode('direction'); direction = 0; }
  else { setMode('state'); state = a.state; const n = STATES[state].durations.length, i = (a.frame + delta + n) % n; elapsed = STATES[state].durations.slice(0, i).reduce((x, y) => x + y, 0); }
  paint();
}
$('play').addEventListener('click', () => {
  if (['direction', 'neutral', 'pointer'].includes(mode)) { setMode('look-loop'); elapsed = (direction ?? 0) * 160; }
  playing = !playing; paint();
});
$('previous').addEventListener('click', () => step(-1)); $('next').addEventListener('click', () => step(1));
$('neutral').addEventListener('click', () => { setMode('neutral'); playing = false; paint(); });
$('look-loop').addEventListener('click', () => { setMode('look-loop'); elapsed = 0; playing = true; paint(); });
$('pointer').addEventListener('click', () => { setMode('pointer'); direction = null; playing = false; paint(); });
$('interactive').addEventListener('click', () => {
  cancelInteraction(); interaction.reset(performance.now());
  interaction.setActivity($('activity').value, performance.now());
  setMode('interactive'); paint();
});
$('reset-position').addEventListener('click', () => { cancelInteraction(); offset = { x: 0, y: 0 }; positionPet(); paint(); });
$('activity').addEventListener('change', () => { interaction.setActivity($('activity').value, performance.now()); paint(); });
$('reduced-motion').addEventListener('change', () => { interaction.reducedMotion = $('reduced-motion').checked; paint(); });
motionPreference.addEventListener('change', e => { interaction.reducedMotion = e.matches; $('reduced-motion').checked = e.matches; paint(); });

function pointerPoint(e) {
  const b = canvas.getBoundingClientRect(), s = stage.getBoundingClientRect();
  const px = Math.floor((e.clientX - b.left) / b.width * CELL.width);
  const py = Math.floor((e.clientY - b.top) / b.height * CELL.height);
  const inside = px >= 0 && px < CELL.width && py >= 0 && py < CELL.height;
  return {
    id: e.pointerId, x: e.clientX - s.left, y: e.clientY - s.top,
    dx: e.clientX - b.left - b.width / 2, dy: e.clientY - b.top - b.height / 2,
    overPet: ready && inside && ctx.getImageData(px, py, 1, 1).data[3] > 32
  };
}
function moveGesture(e) {
  if (!gesture || !interaction.press?.dragging) return;
  offset = { x: gesture.offset.x + e.clientX - gesture.x, y: gesture.offset.y + e.clientY - gesture.y };
  positionPet();
}
stage.addEventListener('pointermove', e => {
  if (!e.isPrimary) return;
  if (mode === 'pointer') {
    const b = canvas.getBoundingClientRect();
    direction = pointerDirection(e.clientX - b.left - b.width / 2, e.clientY - b.top - b.height / 2); paint();
  } else if (mode === 'interactive') {
    interaction.updatePointer(pointerPoint(e), performance.now()); moveGesture(e);
    // Recompute gaze relative to the pet's new position after a drag.
    if (interaction.press?.dragging) interaction.updatePointer(pointerPoint(e), performance.now());
    paint();
  }
});
stage.addEventListener('pointerleave', () => {
  if (mode === 'pointer') { direction = null; paint(); }
  if (mode === 'interactive' && !gesture) { interaction.leave(); paint(); }
});
canvas.addEventListener('pointerdown', e => {
  if (mode !== 'interactive' || !e.isPrimary || e.button !== 0) return;
  if (!interaction.pointerDown(pointerPoint(e), performance.now())) return;
  gesture = { id: e.pointerId, x: e.clientX, y: e.clientY, offset: { ...offset } };
  canvas.setPointerCapture(e.pointerId); canvas.focus({ preventScroll: true }); e.preventDefault(); paint();
});
canvas.addEventListener('pointerup', e => {
  if (mode !== 'interactive' || gesture?.id !== e.pointerId) return;
  interaction.updatePointer(pointerPoint(e), performance.now()); moveGesture(e);
  interaction.pointerUp(pointerPoint(e), performance.now());
  releaseGesture();
  // A captured pointer may be released beyond the stage.
  const b = stage.getBoundingClientRect();
  if (e.clientX < b.left || e.clientX > b.right || e.clientY < b.top || e.clientY > b.bottom) interaction.leave();
  paint();
});
canvas.addEventListener('pointercancel', e => {
  if (gesture?.id === e.pointerId) { cancelInteraction(); paint(); }
});
canvas.addEventListener('lostpointercapture', e => {
  if (gesture?.id === e.pointerId) { cancelInteraction(); paint(); }
});
canvas.addEventListener('keydown', e => {
  if (mode !== 'interactive') return;
  if (['Enter', ' '].includes(e.key)) {
    e.preventDefault();
    if (!e.repeat) { interaction.react(performance.now()); paint(); }
  } else if (e.key === 'Escape') { cancelInteraction(); paint(); }
});
window.addEventListener('blur', () => { if (mode === 'interactive') { cancelInteraction(); paint(); } });
window.addEventListener('resize', positionPet);
$('speed').addEventListener('change', () => { speed = Number($('speed').value); });
$('background').addEventListener('change', () => { stage.dataset.background = $('background').value; });
$('zoom').addEventListener('change', () => {
  cancelInteraction();
  const z = Number($('zoom').value);
  canvas.style.width = CELL.width * z + 'px'; canvas.style.height = CELL.height * z + 'px';
  document.querySelector('.scale-note').textContent = z === 1 ? '192 × 208 · 实际宠物尺寸' : z + '× · ' + (z < 1 ? '缩小检查' : '放大检查');
  stage.style.height = Math.max(390, 208 * z + 64) + 'px'; positionPet(); paint();
});
image.onload = () => {
  if (image.naturalWidth !== 1536 || image.naturalHeight !== 2288) { $('asset-status').textContent = '图集尺寸错误：需要1536×2288'; return; }
  ready = true; $('asset-status').textContent = '舒缓亲近版 · v2 · 9组动作 / 16方向' + (requested ? ' · 候选版本' : '');
  paint();
};
image.onerror = () => { $('asset-status').textContent = '图集未能读取，请从仓库根目录启动本地HTTP服务。'; };
const requested = new URLSearchParams(location.search).get('atlas');
image.src = requested && !requested.startsWith('/') && /^[a-zA-Z0-9_./-]+$/.test(requested) ? requested : '../spritesheet.webp?v=calm-8d80bacfcb66';
function tick(now) {
  if (mode === 'interactive') paint(now);
  else if (last && playing) { elapsed += Math.min(now - last, 250) * speed; paint(now); }
  last = now; requestAnimationFrame(tick);
}
setMode('state'); requestAnimationFrame(tick);
