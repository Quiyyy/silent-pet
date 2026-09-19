import { STATES, frameAt, pointerDirection } from './model.mjs';

const reactionDurationsMs = Object.freeze([400, 500, 650, 500, 350]);

export const INTERACTION = Object.freeze({
  enterRadius: 180,
  exitRadius: 210,
  hoverDwellMs: 500,
  cooldownMs: 4000,
  reactionDurationsMs,
  reactionDurationMs: reactionDurationsMs.reduce((sum, duration) => sum + duration, 0),
  dragThreshold: 8,
  directionHysteresisDegrees: 3
});

function reactionFrameAt(elapsed) {
  let phase = Math.max(0, elapsed);
  for (let i = 0; i < reactionDurationsMs.length; i++) {
    if (phase < reactionDurationsMs[i]) return i;
    phase -= reactionDurationsMs[i];
  }
  return reactionDurationsMs.length - 1;
}

export function clampOffset(offset, stage, pet, padding = 12) {
  const x = Math.max(0, (stage.width - pet.width) / 2 - padding);
  const y = Math.max(0, (stage.height - pet.height) / 2 - padding);
  return { x: Math.max(-x, Math.min(x, offset.x)), y: Math.max(-y, Math.min(y, offset.y)) };
}

export class PetInteraction {
  constructor({ reducedMotion = false } = {}) {
    this.reducedMotion = reducedMotion;
    this.reset(0);
  }
  reset(now) {
    this.startedAt = now;
    this.activity = 'idle';
    this.activityAt = now;
    this.pointer = null;
    this.near = false;
    this.gaze = null;
    this.press = null;
    this.reactionAt = null;
    this.reactionId = 0;
    this.reactionSource = null;
    this.cooldownUntil = now;
    this.hoverAt = null;
    this.hoverUsed = false;
    this.dragDirection = null;
    this.dragAt = now;
  }
  setActivity(state, now) {
    if (!STATES[state]) throw new Error('Unknown activity: ' + state);
    this.activity = state;
    this.activityAt = now;
    this.reactionAt = null;
    this.hoverAt = state === 'idle' && this.pointer?.overPet ? now : null;
    this.hoverUsed = false;
  }
  updatePointer(point, now) {
    if (this.press && point.id !== this.press.id) return;
    const wasOver = this.pointer?.overPet ?? false;
    this.pointer = point;
    const distance = Math.hypot(point.dx, point.dy);
    this.near = distance <= (this.near ? INTERACTION.exitRadius : INTERACTION.enterRadius);
    if (point.overPet && !wasOver) {
      this.hoverAt = now;
      this.hoverUsed = false;
    } else if (!point.overPet) {
      this.hoverAt = null;
      this.hoverUsed = false;
    }
    if (!this.press) return;
    const p = this.press;
    const dx = point.x - p.x, dy = point.y - p.y;
    if (Math.hypot(dx, dy) >= INTERACTION.dragThreshold && !p.dragging) {
      p.dragging = true;
      this.dragAt = now;
      this.reactionAt = null;
    }
    if (p.dragging) {
      const delta = point.x - p.lastX;
      if (Math.abs(delta) >= 1) {
        const next = delta > 0 ? 'running-right' : 'running-left';
        if (next !== this.dragDirection) { this.dragDirection = next; this.dragAt = now; }
      }
    }
    p.lastX = point.x;
    p.lastY = point.y;
  }
  pointerDown(point, now) {
    if (!point.overPet || this.press) return false;
    this.updatePointer(point, now);
    this.press = { id: point.id, x: point.x, y: point.y, lastX: point.x, lastY: point.y, dragging: false };
    this.dragDirection = null;
    this.hoverAt = null;
    this.hoverUsed = true;
    return true;
  }
  pointerUp(point, now) {
    if (!this.press || point.id !== this.press.id) return { type: 'ignored' };
    this.updatePointer(point, now);
    const dragged = this.press.dragging;
    this.press = null;
    this.hoverAt = null;
    this.hoverUsed = true;
    if (dragged) return { type: 'drag-end' };
    if (!point.overPet) return { type: 'ignored' };
    return { type: this.react(now, 'click') ? 'reaction' : 'ignored' };
  }
  leave() {
    this.pointer = null;
    this.near = false;
    this.gaze = null;
    this.hoverAt = null;
    this.hoverUsed = false;
  }
  cancel(pointerId) {
    if (pointerId !== undefined && this.press?.id !== pointerId) return;
    this.press = null;
    this.reactionAt = null;
    this.hoverAt = null;
    this.hoverUsed = true;
    this.pointer = null;
    this.near = false;
    this.gaze = null;
  }
  settle(now) {
    if (this.reactionAt !== null && now - this.reactionAt >= INTERACTION.reactionDurationMs) this.reactionAt = null;
  }
  react(now, source = 'keyboard') {
    this.settle(now);
    if (this.activity !== 'idle' || this.press?.dragging || this.reactionAt !== null || now < this.cooldownUntil) return false;
    this.reactionAt = now;
    this.reactionId += 1;
    this.reactionSource = source;
    this.cooldownUntil = now + INTERACTION.cooldownMs;
    this.hoverUsed = true;
    return true;
  }
  gazeDirection() {
    const { dx, dy } = this.pointer;
    const next = pointerDirection(dx, dy);
    if (next === null || this.gaze === null) { this.gaze = next; return next; }
    const angle = (Math.atan2(dx, -dy) * 180 / Math.PI + 360) % 360;
    const delta = ((angle - this.gaze * 22.5 + 540) % 360) - 180;
    if (Math.abs(delta) > 11.25 + INTERACTION.directionHysteresisDegrees) this.gaze = next;
    return this.gaze;
  }
  snapshot(now) {
    this.settle(now);
    if (this.activity === 'idle' && !this.press && this.pointer?.overPet &&
        !this.hoverUsed && this.hoverAt !== null && now - this.hoverAt >= INTERACTION.hoverDwellMs) {
      this.hoverUsed = true; // Consume even during cooldown; never queue a delayed repeat.
      this.react(now, 'hover');
    }
    const common = { reactionId: this.reactionId, source: this.reactionSource, cooldownMs: Math.max(0, this.cooldownUntil - now) };
    if (this.press?.dragging) {
      const state = this.dragDirection ?? 'idle';
      return { ...common, kind: 'drag', state, frame: this.reducedMotion ? 0 : frameAt(state, now - this.dragAt) };
    }
    if (this.activity !== 'idle') {
      return { ...common, kind: 'task', state: this.activity, frame: this.reducedMotion ? 0 : frameAt(this.activity, now - this.activityAt) };
    }
    if (this.reactionAt !== null) {
      return { ...common, kind: 'affection', state: 'jumping', frame: this.reducedMotion ? 2 : reactionFrameAt(now - this.reactionAt) };
    }
    if (this.near && this.pointer) {
      return { ...common, kind: 'gaze', direction: this.gazeDirection() };
    }
    this.gaze = null;
    return { ...common, kind: 'idle', state: 'idle', frame: this.reducedMotion ? 0 : frameAt('idle', now - this.startedAt) };
  }
}
