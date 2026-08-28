const TAU = Math.PI * 2;

const fallback = {
  backend: 'js',
  cosineMagnification01(normalized) {
    const n = Math.max(0, Math.min(1, Number(normalized) || 0));
    return (1 - Math.cos(n * TAU)) / 2;
  },
  springStep(current, target, velocity, stiffness, damping, dt) {
    const acceleration = (target - current) * stiffness - velocity * damping;
    const nextVelocity = velocity + acceleration * dt;
    return current + nextVelocity * dt;
  },
};

window.AppleOSMath = fallback;
window.dispatchEvent(new CustomEvent('appleos:wasm-ready', { detail: { backend: 'js' } }));

async function instantiateMath() {
  const url = new URL('../wasm/appleos_math.wasm', import.meta.url);
  let instance;
  try {
    if (WebAssembly.instantiateStreaming) {
      const result = await WebAssembly.instantiateStreaming(fetch(url), {});
      instance = result.instance;
    } else {
      throw new Error('streaming unavailable');
    }
  } catch {
    const response = await fetch(url);
    const bytes = await response.arrayBuffer();
    const result = await WebAssembly.instantiate(bytes, {});
    instance = result.instance;
  }

  const exports = instance.exports;
  if (typeof exports.cosine_magnification01 !== 'function' || typeof exports.spring_step !== 'function') {
    throw new Error('AppleOS WASM exports missing');
  }

  window.AppleOSMath = {
    backend: 'wasm',
    cosineMagnification01(normalized) {
      const n = Math.max(0, Math.min(1, Number(normalized) || 0));
      const value = exports.cosine_magnification01(n);
      return Number.isFinite(value) ? Math.max(0, Math.min(1, value)) : fallback.cosineMagnification01(n);
    },
    springStep(current, target, velocity, stiffness, damping, dt) {
      const value = exports.spring_step(current, target, velocity, stiffness, damping, dt);
      return Number.isFinite(value) ? value : fallback.springStep(current, target, velocity, stiffness, damping, dt);
    },
  };
  window.dispatchEvent(new CustomEvent('appleos:wasm-ready', { detail: { backend: 'wasm' } }));
}

instantiateMath().catch(() => {
  window.AppleOSMath = fallback;
  window.dispatchEvent(new CustomEvent('appleos:wasm-ready', { detail: { backend: 'js' } }));
});

export { fallback };
