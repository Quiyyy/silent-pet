import test from 'node:test';
import assert from 'node:assert/strict';
import { STATES,CELL,DIRECTIONS,duration,frameAt,directionCell,pointerDirection,sequenceAt,SEQUENCES } from '../preview/model.mjs';
test('nine states have the app frame counts and exact boundary timing',()=>{
 assert.deepEqual(Object.values(STATES).map(s=>s.durations.length),[6,8,8,4,5,8,6,6,6]);
 for(const [name,s] of Object.entries(STATES)){
  let sum=0;s.durations.forEach((ms,i)=>{assert.equal(frameAt(name,sum),i);assert.equal(frameAt(name,sum+ms-0.001),i);sum+=ms;});
  assert.equal(frameAt(name,sum),0);assert.equal(frameAt(name,sum*100+1),0);
 }
 assert.equal(duration('idle'),1100);
});
test('all sixteen directions use the two v2 rows and wrap safely',()=>{
 assert.equal(DIRECTIONS.length,16);assert.deepEqual(directionCell(0),{row:9,column:0});
 assert.deepEqual(directionCell(8),{row:10,column:0});assert.deepEqual(directionCell(15),{row:10,column:7});
 assert.deepEqual(directionCell(16),directionCell(0));assert.deepEqual(directionCell(-1),directionCell(15));
 for(let i=0;i<16;i++){const c=directionCell(i);assert.ok(c.row<CELL.rows&&c.column<CELL.columns);}
});
test('screen-coordinate gaze has correct quadrants, cardinal axes and deadzone',()=>{
 assert.equal(pointerDirection(0,-100),0);assert.equal(pointerDirection(100,0),4);
 assert.equal(pointerDirection(0,100),8);assert.equal(pointerDirection(-100,0),12);
 assert.equal(pointerDirection(100,100),6);assert.equal(pointerDirection(-100,100),10);
 assert.equal(pointerDirection(-100,-100),14);assert.equal(pointerDirection(100,-100),2);
 assert.equal(pointerDirection(0,0),null);assert.equal(pointerDirection(8,0),null);
 for(let i=0;i<16;i++){const angle=i*Math.PI/8;assert.equal(pointerDirection(Math.sin(angle)*100,-Math.cos(angle)*100),i);}
});
test('transition scenarios visit every requested state at original loop boundaries',()=>{
 for(const [name,s] of Object.entries(SEQUENCES)){
  let offset=0;s.states.forEach((state,index)=>{const start=sequenceAt(name,offset);assert.equal(start.state,state);assert.equal(start.index,index);assert.equal(start.elapsed,0);assert.equal(sequenceAt(name,offset+duration(state)*2-0.001).state,state);offset+=duration(state)*2;});
  assert.deepEqual(sequenceAt(name,offset),{state:s.states[0],elapsed:0,index:0});
 }
});
