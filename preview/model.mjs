export const CELL = Object.freeze({ width: 192, height: 208, columns: 8, rows: 11 });
export const STATES = Object.freeze({
  idle: { label: '安静待机', row: 0, durations: [280,110,110,140,140,320] },
  'running-right': { label: '向右跑', row: 1, durations: [120,120,120,120,120,120,120,220] },
  'running-left': { label: '向左跑', row: 2, durations: [120,120,120,120,120,120,120,220] },
  waving: { label: '招手', row: 3, durations: [140,140,140,280] },
  jumping: { label: '亲近回应', row: 4, durations: [140,140,140,140,280] },
  failed: { label: '失落', row: 5, durations: [140,140,140,140,140,140,140,240] },
  waiting: { label: '等待回应', row: 6, durations: [150,150,150,150,150,260] },
  running: { label: '寻找线索', row: 7, durations: [120,120,120,120,120,220] },
  review: { label: '完成检查', row: 8, durations: [150,150,150,150,150,280] }
});
export const DIRECTIONS = Array.from({ length: 16 }, (_, i) => i * 22.5);
export const SEQUENCES = Object.freeze({
  work: { label: '工作 → 等待 → 完成', states: ['idle','running','waiting','running','review','idle'] },
  drag: { label: '待机 → 左右拖动 → 松手', states: ['idle','running-right','idle','running-left','idle'] },
  hop: { label: '待机 → 亲近 → 安静', states: ['idle','jumping','idle','jumping','idle'] }
});
export function duration(state) { return STATES[state].durations.reduce((a,b)=>a+b,0); }
export function frameAt(state, elapsed) {
  const d = STATES[state].durations;
  let phase = ((elapsed % duration(state)) + duration(state)) % duration(state);
  for (let i=0; i<d.length; i++) { if (phase<d[i]) return i; phase-=d[i]; }
  return 0;
}
export function directionCell(index) {
  const i = ((index % 16) + 16) % 16;
  return { row: 9 + Math.floor(i / 8), column: i % 8 };
}
export function pointerDirection(dx,dy) {
  if (Math.hypot(dx,dy) <= 8) return null;
  return Math.round(((Math.atan2(dx,-dy)*180/Math.PI+360)%360)/22.5)%16;
}
export function sequenceAt(name,elapsed) {
  const states = SEQUENCES[name].states;
  const total = states.reduce((sum,s)=>sum+duration(s)*2,0);
  let phase = ((elapsed % total)+total)%total;
  for (let i=0;i<states.length;i++) {
    const state=states[i], length=duration(state)*2;
    if (phase<length) return { state, elapsed:phase, index:i };
    phase-=length;
  }
  return { state:states[0],elapsed:0,index:0 };
}
