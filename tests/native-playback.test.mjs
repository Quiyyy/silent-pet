import test from 'node:test';
import assert from 'node:assert/strict';
import { nativeFrameAt, nativeSequenceAt } from '../preview/native-playback.mjs';
import { STATES, duration, frameAt } from '../preview/model.mjs';

test('desktop idle uses 6600 ms, while frame inspection retains the raw 1100 ms cycle', () => {
  assert.equal(nativeFrameAt('idle', 1679).frame, 0);
  assert.equal(nativeFrameAt('idle', 1680).frame, 1);
  assert.equal(nativeFrameAt('idle', 6600).frame, 0);
  assert.equal(nativeFrameAt('idle', 280).frame, 0);
  assert.equal(frameAt('idle', 280), 1);
});

test('each desktop action plays three rounds then returns to slow idle without losing task identity', () => {
  for (const state of Object.keys(STATES).filter(state => state !== 'idle')) {
    const end = duration(state) * 3;
    assert.equal(nativeFrameAt(state, end - 0.01).state, state);
    assert.deepEqual(nativeFrameAt(state, end), { requestedState: state, state: 'idle', frame: 0, phase: 'idle-return' });
    assert.equal(nativeFrameAt(state, end + 1680).frame, 1);
    assert.equal(nativeFrameAt(state, end + 6600).frame, 0);
  }
  assert.equal(nativeFrameAt('jumping', 2519).state, 'jumping');
  assert.equal(nativeFrameAt('jumping', 2520).state, 'idle');
  assert.equal(nativeFrameAt('waving', 2100).state, 'idle');
});

test('reduced motion stays at the requested first frame even past the normal return time', () => {
  for (const state of Object.keys(STATES)) {
    assert.deepEqual(nativeFrameAt(state, 100000, { reducedMotion: true }), { requestedState: state, state, frame: 0, phase: 'reduced' });
  }
});

test('desktop scenario preserves slow idle and includes the automatic idle return', () => {
  assert.equal(nativeSequenceAt('work', 6599).requestedState, 'idle');
  assert.equal(nativeSequenceAt('work', 6600).requestedState, 'running');
  const afterWork = 6600 + duration('running') * 3;
  assert.equal(nativeSequenceAt('work', afterWork).phase, 'idle-return');
  assert.equal(nativeSequenceAt('work', afterWork + 6600).requestedState, 'waiting');
});
