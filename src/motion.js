/* NOIR motion controller. Dependency-free; shared by browser and numerical tests.
 * Repeated real poles: (D + omega)^3 e = 0. Exact integration preserves position,
 * velocity AND acceleration on retarget. Radius travels in logarithmic space.
 * phi is elevation in the existing renderer, NOT a Three.js polar angle.
 */
(function (root) {
  'use strict';
  const KEYS = ['theta', 'phi', 'radius', 'y', 'sx', 'sy'];
  const TAU = Math.PI * 2;
  const shortestAngle = (from, to) => Math.abs(to - from) <= Math.PI ? to
    : from + ((to - from + Math.PI) % TAU + TAU) % TAU - Math.PI;
  function validate(pose) {
    if (!pose || KEYS.some(key => !Number.isFinite(pose[key])) || pose.radius <= 0) {
      throw new TypeError('Camera pose must contain six finite axes and a positive radius.');
    }
  }
  class Controller {
    constructor(pose, omega = 9.25) {
      validate(pose);
      if (!Number.isFinite(omega) || omega <= 0) throw new RangeError('omega must be positive.');
      this.omega = omega;
      this.axes = {};
      this.pose = {};
      this.reset(pose);
    }
    reset(pose) {
      validate(pose);
      for (const key of KEYS) {
        const x = key === 'radius' ? Math.log(pose[key]) : pose[key];
        this.axes[key] = { x, v: 0, a: 0, target: x };
        this.pose[key] = pose[key];
      }
      this.active = false;
      return this.pose;
    }
    retarget(pose) {
      validate(pose);
      // Only destinations change. Current values/derivatives are never reinitialised.
      for (const key of KEYS) {
        const s = this.axes[key];
        s.target = key === 'theta' ? shortestAngle(s.x, pose[key])
          : key === 'radius' ? Math.log(pose[key]) : pose[key];
      }
      this.active = !this.isSettled();
    }
    step(dt) {
      if (!Number.isFinite(dt) || dt < 0) throw new RangeError('dt must be finite and nonnegative.');
      if (!this.active || dt === 0) return this.pose;
      // A dropped frame must not teleport the camera. Normal 30–144 Hz is exact.
      const t = Math.min(dt, 0.064), w = this.omega, decay = Math.exp(-w * t);
      for (const key of KEYS) {
        const s = this.axes[key], e = s.x - s.target;
        const b = s.v + w * e, c = (s.a + 2 * w * s.v + w * w * e) / 2;
        const p = e + b * t + c * t * t, dp = b + 2 * c * t;
        s.x = s.target + p * decay;
        s.v = (dp - w * p) * decay;
        s.a = (2 * c - 2 * w * dp + w * w * p) * decay;
        this.pose[key] = key === 'radius' ? Math.exp(s.x) : s.x;
      }
      if (this.isSettled()) {
        // Residual below 0.01 screen pixels at the supported compositions.
        for (const key of KEYS) {
          const s = this.axes[key]; s.x = s.target; s.v = 0; s.a = 0;
          this.pose[key] = key === 'radius' ? Math.exp(s.x) : s.x;
        }
        this.active = false;
      }
      return this.pose;
    }
    isSettled() {
      return KEYS.every(key => {
        const s = this.axes[key];
        return Math.abs(s.x - s.target) < 0.00001 && Math.abs(s.v) < 0.0001 && Math.abs(s.a) < 0.001;
      });
    }
    get nearDestination() {
      return KEYS.every(key => {
        const s = this.axes[key];
        return Math.abs(s.x - s.target) < 0.006 && Math.abs(s.v) < 0.045;
      });
    }
    snapshot() {
      return Object.fromEntries(KEYS.map(key => [key, { ...this.axes[key] }]));
    }
  }
  const api = { Controller, shortestAngle, KEYS };
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.NoirMotion = api;
})(typeof window === 'undefined' ? globalThis : window);
