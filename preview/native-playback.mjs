import { STATES, SEQUENCES, duration, frameAt } from './model.mjs';

// Verified against desktop 26.1002.52244 on 2026-10-15.
// These are renderer rules, not fields accepted by pet.json.
export const NATIVE_PLAYBACK = Object.freeze({ idleSlowdown: 6, actionRepeats: 3 });

export function nativeFrameAt(requestedState, elapsed, { reducedMotion = false } = {}) {
  if (!STATES[requestedState]) throw new Error('Unknown state: ' + requestedState);
  const time = Math.max(0, elapsed);
  if (reducedMotion) return { requestedState, state: requestedState, frame: 0, phase: 'reduced' };
  const actionEnd = requestedState === 'idle' ? 0 : duration(requestedState) * NATIVE_PLAYBACK.actionRepeats;
  if (time < actionEnd) {
    return { requestedState, state: requestedState, frame: frameAt(requestedState, time), phase: 'action' };
  }
  return {
    requestedState,
    state: 'idle',
    frame: frameAt('idle', (time - actionEnd) / NATIVE_PLAYBACK.idleSlowdown),
    phase: requestedState === 'idle' ? 'idle' : 'idle-return'
  };
}

export function nativeSequenceAt(name, elapsed, options) {
  const states = SEQUENCES[name].states;
  const idleMs = duration('idle') * NATIVE_PLAYBACK.idleSlowdown;
  const lengths = states.map(state => idleMs + (state === 'idle' ? 0 : duration(state) * NATIVE_PLAYBACK.actionRepeats));
  const total = lengths.reduce((a, b) => a + b, 0);
  let phase = ((elapsed % total) + total) % total;
  for (let index = 0; index < states.length; index++) {
    if (phase < lengths[index]) return { ...nativeFrameAt(states[index], phase, options), index };
    phase -= lengths[index];
  }
  return { ...nativeFrameAt(states[0], 0, options), index: 0 };
}
