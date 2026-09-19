import test from 'node:test';
import assert from 'node:assert/strict';
import { PetInteraction, INTERACTION, clampOffset } from '../preview/interaction.mjs';
import { duration } from '../preview/model.mjs';
const point=(x=0,y=0,overPet=true,id=1)=>({x,y,dx:x,dy:y,overPet,id});
test('proximity enters, uses hysteresis, leaves and respects center deadzone',()=>{
 const p=new PetInteraction();
 p.updatePointer(point(179,0,false),0);assert.equal(p.snapshot(0).direction,4);
 p.updatePointer(point(200,0,false),1);assert.equal(p.snapshot(1).kind,'gaze');
 p.updatePointer(point(211,0,false),2);assert.equal(p.snapshot(2).kind,'idle');
 p.updatePointer(point(190,0,false),3);assert.equal(p.snapshot(3).kind,'idle');
 p.updatePointer(point(0,0,false),4);assert.equal(p.snapshot(4).direction,null);
 p.leave();assert.equal(p.snapshot(5).kind,'idle');
});
test('quick click plays one reaction, returns to gaze, and cooldown rejects repeats',()=>{
 const p=new PetInteraction();p.pointerDown(point(),0);assert.equal(p.pointerUp(point(),50).type,'reaction');
 assert.equal(p.snapshot(50).kind,'affection');assert.equal(p.snapshot(50).frame,0);
 assert.equal(p.snapshot(50+duration('jumping')).kind,'gaze');
 p.pointerDown(point(),900);p.pointerUp(point(),920);assert.equal(p.reactionId,1);
 assert.equal(p.react(50+INTERACTION.cooldownMs-1),false);
 assert.equal(p.react(50+INTERACTION.cooldownMs),true);
});
test('hover dwell is one-shot per entry, including after cooldown expires',()=>{
 const p=new PetInteraction();p.updatePointer(point(),0);
 assert.notEqual(p.snapshot(349).kind,'affection');
 assert.equal(p.snapshot(350).kind,'affection');
 assert.notEqual(p.snapshot(10000).kind,'affection');assert.equal(p.reactionId,1);
 p.leave();p.updatePointer(point(),10001);p.snapshot(10351);assert.equal(p.reactionId,2);
});
test('hover entered during cooldown is consumed instead of queued for later',()=>{
 const p=new PetInteraction();p.react(0);p.leave();p.updatePointer(point(),900);p.snapshot(1250);
 p.snapshot(5000);assert.equal(p.reactionId,1);
});
test('drag outranks an active reaction; release never becomes affection click',()=>{
 const p=new PetInteraction();p.react(0);p.pointerDown(point(),100);
 p.updatePointer(point(20,0),120);assert.equal(p.snapshot(120).kind,'drag');
 assert.equal(p.snapshot(120).state,'running-right');
 p.updatePointer(point(5,0),150);assert.equal(p.snapshot(150).state,'running-left');
 assert.equal(p.pointerUp(point(5,0),180).type,'drag-end');assert.equal(p.reactionId,1);
 assert.notEqual(p.snapshot(200).kind,'affection');
});
test('release displacement without an intermediate move still counts as drag',()=>{
 const p=new PetInteraction();p.pointerDown(point(),0);
 assert.equal(p.pointerUp(point(0,20,false),100).type,'drag-end');assert.equal(p.reactionId,0);
});
test('pointer cancel, mismatched pointer and release outside do not create clicks',()=>{
 const p=new PetInteraction();p.pointerDown(point(),0);assert.equal(p.pointerDown(point(0,0,true,2),1),false);
 assert.equal(p.pointerUp(point(0,0,true,2),2).type,'ignored');assert.equal(p.press.id,1);
 p.cancel(1);assert.equal(p.pointerUp(point(),100).type,'ignored');assert.equal(p.snapshot(200).kind,'idle');
 p.pointerDown(point(),300);assert.equal(p.pointerUp(point(1,1,false),320).type,'ignored');assert.equal(p.reactionId,0);
});
test('task activity suppresses gaze/affection and clears a running reaction',()=>{
 const p=new PetInteraction();p.react(0);p.setActivity('waiting',100);p.updatePointer(point(),101);
 assert.equal(p.snapshot(1000).state,'waiting');assert.equal(p.snapshot(1000).kind,'task');assert.equal(p.react(5000),false);
 p.setActivity('idle',5100);assert.equal(p.react(5100),true);
});
test('reduced-motion keeps reaction and task frames static',()=>{
 const p=new PetInteraction({reducedMotion:true});p.react(0);
 assert.equal(p.snapshot(10).frame,2);assert.equal(p.snapshot(600).frame,2);
 p.setActivity('running',700);assert.equal(p.snapshot(950).frame,0);
});
test('drag offset is clamped to stage bounds even if viewport is smaller than pet',()=>{
 assert.deepEqual(clampOffset({x:999,y:-999},{width:400,height:300},{width:192,height:208}),{x:92,y:-34});
 assert.deepEqual(clampOffset({x:99,y:99},{width:100,height:100},{width:192,height:208}),{x:0,y:0});
});

test('gaze does not flicker at a direction boundary and wraps across north',()=>{
 const p=new PetInteraction();
 const at=angle=>{const a=angle*Math.PI/180;return point(100*Math.sin(a),-100*Math.cos(a),false);};
 p.updatePointer(at(10),0);assert.equal(p.snapshot(0).direction,0);
 for(const a of [11,12,11,14]){p.updatePointer(at(a),1);assert.equal(p.snapshot(1).direction,0);}
 p.updatePointer(at(16),2);assert.equal(p.snapshot(2).direction,1);
 p.updatePointer(at(12),3);assert.equal(p.snapshot(3).direction,1);
 p.updatePointer(at(5),4);assert.equal(p.snapshot(4).direction,0);
 p.updatePointer(at(350),5);assert.equal(p.snapshot(5).direction,0);
 p.updatePointer(at(344),6);assert.equal(p.snapshot(6).direction,15);
 p.leave();p.updatePointer(at(359),7);assert.equal(p.snapshot(7).direction,0);
});
