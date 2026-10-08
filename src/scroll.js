/* Input routing only. Authored poses, renderer, styling and motion are unchanged. */
(function (root) {
'use strict';
const THRESHOLD = 36, GAP = 180, REPEAT = 650, EDGE = 1;
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

// A gesture belongs either to panel reading or to section navigation, never both.
// A falling momentum tail cannot turn a panel scroll into an accidental page change.
class WheelIntent {
 constructor() { this.reset(); }
 reset() {
  this.lastAt = -Infinity; this.startedAt = 0; this.direction = 0;
  this.sum = 0; this.reverseSum = 0; this.peak = 0; this.previous = 0;
  this.owner = null; this.consumed = false;
 }
 read(delta, now, nativeAvailable = false) {
  const magnitude = Math.abs(delta), direction = Math.sign(delta);
  if (!Number.isFinite(delta) || magnitude < .2) return {prevent: false, step: 0};
  const gap = now - this.lastAt;
  let fresh = gap > GAP, carry = magnitude;
  // Slow, small wheel notches may span separate event bursts. Keep unfinished
  // intent briefly, but never carry a consumed gesture or panel-reading distance.
  const pending = fresh && gap <= 500 && !this.consumed && this.owner === 'scene' && direction === this.direction ? this.sum : 0;
  if (!fresh && direction !== this.direction) {
   // Small opposite-sign trackpad noise must not re-arm a consumed gesture.
   this.reverseSum += magnitude;
   this.lastAt = now;
   if (!(nativeAvailable && this.owner === 'native') && this.reverseSum < THRESHOLD)
    return {prevent: true, step: 0};
   carry = this.reverseSum; fresh = true;
  } else this.reverseSum = 0;
  if (!fresh && (this.consumed || this.owner === 'native') && now - this.startedAt >= REPEAT) {
   const renewed = magnitude >= 12 && magnitude >= this.previous * 1.8 && magnitude >= this.peak * .6;
   const repeatedNotch = magnitude >= Math.max(16, this.peak * .8);
   fresh = renewed || repeatedNotch;
  }
  if (fresh) {
   this.direction = direction; this.sum = pending; this.reverseSum = 0;
   this.owner = null; this.consumed = false; this.peak = 0; this.startedAt = now;
  }
  this.lastAt = now; this.previous = magnitude; this.peak = Math.max(this.peak, magnitude);
  if (!this.owner) this.owner = nativeAvailable ? 'native' : 'scene';
  if (this.owner === 'native') return {prevent: !nativeAvailable, step: 0};
  if (this.consumed) return {prevent: true, step: 0};
  this.sum += carry;
  if (this.sum < THRESHOLD) return {prevent: true, step: 0};
  this.consumed = true;
  return {prevent: true, step: direction};
 }
}

function install({app, content, step, getSection, blocked}) {
 const wheel = new WheelIntent();
 let expectedSection = getSection(), touch = null;
 const elementOf = target => target?.nodeType === 1 ? target : target?.parentElement;
 const ignored = target => blocked() || !!target?.closest(editable);
 const nativeAvailable = (target, direction) => content.contains(target) && canScroll(content, direction);
 function syncSection() {
  if (getSection() !== expectedSection) { wheel.reset(); touch = null; expectedSection = getSection(); }
 }
 function navigate(direction) { step(direction); expectedSection = getSection(); }
 function onWheel(event) {
  syncSection();
  const target = elementOf(event.target), delta = normalizeWheel(event, app.clientHeight);
  if (event.defaultPrevented || event.ctrlKey || event.metaKey || ignored(target)) { wheel.reset(); return; }
  if (!delta.y || Math.abs(delta.x) > Math.abs(delta.y)) return;
  const decision = wheel.read(delta.y, performance.now(), nativeAvailable(target, Math.sign(delta.y)));
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
  touch = {id: point.identifier, x: point.clientX, y: point.clientY, target, owner: null, done: false};
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
  if (!touch.done && Math.abs(dy) >= 55) { touch.done = true; navigate(Math.sign(dy)); }
 }
 function onTouchEnd() { touch = null; }
 function onVisibility() { wheel.reset(); touch = null; }
 app.addEventListener('wheel', onWheel, {passive: false});
 app.addEventListener('touchstart', onTouchStart, {passive: true});
 app.addEventListener('touchmove', onTouchMove, {passive: false});
 app.addEventListener('touchend', onTouchEnd, {passive: true});
 app.addEventListener('touchcancel', onTouchEnd, {passive: true});
 document.addEventListener('visibilitychange', onVisibility);
 return () => {
  app.removeEventListener('wheel', onWheel);
  app.removeEventListener('touchstart', onTouchStart); app.removeEventListener('touchmove', onTouchMove);
  app.removeEventListener('touchend', onTouchEnd); app.removeEventListener('touchcancel', onTouchEnd);
  document.removeEventListener('visibilitychange', onVisibility);
 };
}
const api = {WheelIntent, normalizeWheel, canScroll, install};
if (typeof module !== 'undefined' && module.exports) module.exports = api;
else root.NoirScroll = api;
})(typeof window === 'undefined' ? globalThis : window);
