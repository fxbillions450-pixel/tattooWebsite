/* NOIR input routing. Navigation follows distance, never camera completion. */
(function (root) {
'use strict';
const THRESHOLD = 36, STRIDE = 96, GAP = 180, EDGE = 1;
const editable = 'input,textarea,select,[contenteditable]:not([contenteditable="false"])';

function normalizeWheel(event, pageHeight = 800) {
 const scale = event.deltaMode === 1 ? 16 : event.deltaMode === 2 ? pageHeight : 1;
 return {x: event.deltaX * scale, y: event.deltaY * scale};
}
function canScroll(element, direction) {
 if (!element || element.scrollHeight <= element.clientHeight + EDGE) return false;
 const top = Math.max(0, element.scrollTop);
 return direction < 0 ? top > EDGE : top < element.scrollHeight - element.clientHeight - EDGE;
}

// Scene strokes can cross multiple destinations. No consumed-gesture latch,
// repeat cooldown, peak-strength test, landing test, queue or deferred replay.
// Momentum contributes distance just like ordinary scrolling; a long flick may
// intentionally cross several sections. Tiny residual movement is accumulated,
// not amplified into a full section on every event.
class WheelIntent {
 constructor() { this.reset(); }
 reset() {
  this.lastAt = -Infinity; this.direction = 0; this.sum = 0;
  this.reverseSum = 0; this.owner = null; this.started = false;
 }
 read(delta, now, nativeAvailable = false) {
  const magnitude = Math.abs(delta), direction = Math.sign(delta);
  if (!Number.isFinite(delta) || !Number.isFinite(now) || magnitude < .2)
   return {prevent: false, step: 0};
  const gap = now - this.lastAt;
  if (gap > GAP || gap < 0) {
   // Preserve incomplete, slow small notches for up to half a second.
   const pending = gap <= 500 && !this.started && this.owner === 'scene' && direction === this.direction ? this.sum : 0;
   this.reset(); this.sum = pending; this.direction = direction;
  }
  this.lastAt = now;
  if (direction !== this.direction) {
   if (this.owner === 'native' && nativeAvailable) {
    this.direction = direction; this.reverseSum = 0;
   } else {
    this.reverseSum += magnitude;
    if (this.reverseSum < THRESHOLD) return {prevent: true, step: 0};
    // Reverse immediately from the latest destination; no forward debt.
    this.direction = direction; this.sum = 0; this.reverseSum = 0;
    this.owner = nativeAvailable ? 'native' : 'scene'; this.started = this.owner === 'scene';
    return {prevent: this.owner === 'scene', step: this.owner === 'scene' ? direction : 0};
   }
  } else this.reverseSum = 0;
  if (!this.owner) this.owner = nativeAvailable ? 'native' : 'scene';
  // Reading retains native scroll and cannot leak across an edge in the same
  // stroke. A fresh outward stroke at the edge belongs to the scene instead.
  if (this.owner === 'native') return {prevent: !nativeAvailable, step: 0};
  this.sum += Math.min(magnitude, STRIDE);
  const threshold = this.started ? STRIDE : THRESHOLD;
  if (this.sum < threshold) return {prevent: true, step: 0};
  this.sum = this.started ? this.sum - threshold : 0; this.started = true;
  return {prevent: true, step: direction};
 }
}

function install({app, content, step, getSection, blocked}) {
 const wheel = new WheelIntent();
 let expectedSection = getSection(), touch = null;
 const elementOf = target => target?.nodeType === 1 ? target : target?.parentElement;
 const ignored = target => blocked() || !!target?.closest(editable);
 const nativeAvailable = (target, direction) => !content.closest('[inert]') && content.contains(target) && canScroll(content, direction);
 function syncSection() {
  if (getSection() !== expectedSection) { wheel.reset(); touch = null; expectedSection = getSection(); }
 }
 function navigate(direction) { step(direction); expectedSection = getSection(); }
 function onWheel(event) {
  syncSection();
  const target = elementOf(event.target), delta = normalizeWheel(event, app.clientHeight);
  if (event.defaultPrevented || event.ctrlKey || event.metaKey || ignored(target)) { wheel.reset(); return; }
  if (!delta.y || Math.abs(delta.x) > Math.abs(delta.y)) return;
  const now = performance.now(), stamp = event.timeStamp;
  // Capture time remains correct when main-thread rendering delays delivery.
  const inputTime = Number.isFinite(stamp) && Math.abs(stamp - now) < 60000 ? stamp : now;
  const decision = wheel.read(delta.y, inputTime, nativeAvailable(target, Math.sign(delta.y)));
  if (decision.prevent && event.cancelable) event.preventDefault();
  if (decision.step) navigate(decision.step);
 }
 function onTouchStart(event) {
  syncSection(); wheel.reset(); touch = null;
  const target = elementOf(event.target);
  if (event.touches.length !== 1 || ignored(target)) return;
  const point = event.touches[0];
  // Leave OS edge-back gestures alone.
  if (point.clientX < 24 || point.clientX > app.clientWidth - 24) return;
  touch = {id: point.identifier, x: point.clientX, y: point.clientY, lastY: point.clientY,
   target, owner: null, direction: 0, sum: 0, started: false};
 }
 function onTouchMove(event) {
  if (!touch) return;
  if (event.touches.length !== 1 || blocked()) { touch = null; return; }
  const point = Array.from(event.touches).find(t => t.identifier === touch.id);
  if (!point) { touch = null; return; }
  const dx = point.clientX - touch.x, dy = touch.y - point.clientY;
  if (!touch.owner) {
   if (Math.max(Math.abs(dx), Math.abs(dy)) < 8) return;
   if (Math.abs(dx) > Math.abs(dy) / 1.2) { touch.owner = 'native'; return; }
   touch.owner = nativeAvailable(touch.target, Math.sign(dy)) ? 'native' : 'scene';
  }
  if (touch.owner === 'native') return;
  if (event.cancelable) event.preventDefault();
  const delta = touch.lastY - point.clientY; touch.lastY = point.clientY;
  if (!delta) return;
  if (Math.sign(delta) !== touch.direction) {
   touch.direction = Math.sign(delta); touch.sum = 0; touch.started = false;
  }
  touch.sum += Math.abs(delta);
  const threshold = touch.started ? 120 : 55;
  if (touch.sum >= threshold) {
   // A long drag continues through sections without lifting the finger.
   const count = 1 + Math.floor((touch.sum - threshold) / 120);
   touch.sum = (touch.sum - threshold) % 120; touch.started = true;
   navigate(touch.direction * count);
  }
 }
 function resetInput() { wheel.reset(); touch = null; }
 function onTouchEnd() { touch = null; }
 app.addEventListener('wheel', onWheel, {passive: false});
 app.addEventListener('touchstart', onTouchStart, {passive: true});
 app.addEventListener('touchmove', onTouchMove, {passive: false});
 app.addEventListener('touchend', onTouchEnd, {passive: true});
 app.addEventListener('touchcancel', onTouchEnd, {passive: true});
 document.addEventListener('visibilitychange', resetInput);
 root.addEventListener('blur', resetInput);
 return () => {
  app.removeEventListener('wheel', onWheel);
  app.removeEventListener('touchstart', onTouchStart); app.removeEventListener('touchmove', onTouchMove);
  app.removeEventListener('touchend', onTouchEnd); app.removeEventListener('touchcancel', onTouchEnd);
  document.removeEventListener('visibilitychange', resetInput); root.removeEventListener('blur', resetInput);
 };
}
const api = {WheelIntent, normalizeWheel, canScroll, install};
if (typeof module !== 'undefined' && module.exports) module.exports = api;
else root.NoirScroll = api;
})(typeof window === 'undefined' ? globalThis : window);
