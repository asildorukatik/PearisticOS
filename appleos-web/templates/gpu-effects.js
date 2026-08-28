function sizeCanvas(canvas) {
  const dpr = Math.min(2, window.devicePixelRatio || 1);
  const width = Math.max(1, Math.floor(innerWidth * dpr));
  const height = Math.max(1, Math.floor(innerHeight * dpr));
  if (canvas.width !== width || canvas.height !== height) {
    canvas.width = width;
    canvas.height = height;
  }
}

function reducedMotion() {
  return matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? false;
}

async function startWebGPU(canvas) {
  if (!navigator.gpu) throw new Error('WebGPU unavailable');
  const adapter = await navigator.gpu.requestAdapter({ powerPreference: 'low-power' });
  if (!adapter) throw new Error('No WebGPU adapter');
  const device = await adapter.requestDevice();
  const context = canvas.getContext('webgpu');
  if (!context) throw new Error('No WebGPU canvas context');
  const format = navigator.gpu.getPreferredCanvasFormat();

  const configure = () => {
    sizeCanvas(canvas);
    context.configure({ device, format, alphaMode: 'premultiplied' });
  };
  configure();
  addEventListener('resize', configure, { passive: true });

  const draw = (time = 0) => {
    const t = reducedMotion() ? 0 : time * 0.00022;
    const encoder = device.createCommandEncoder();
    const view = context.getCurrentTexture().createView();
    const pass = encoder.beginRenderPass({
      colorAttachments: [{
        view,
        clearValue: {
          r: 0.025 + Math.sin(t) * 0.008,
          g: 0.035 + Math.sin(t * 0.71 + 1.2) * 0.010,
          b: 0.070 + Math.sin(t * 0.53 + 2.1) * 0.018,
          a: 1,
        },
        loadOp: 'clear',
        storeOp: 'store',
      }],
    });
    pass.end();
    device.queue.submit([encoder.finish()]);
    if (!reducedMotion()) requestAnimationFrame(draw);
  };
  requestAnimationFrame(draw);
  return 'webgpu';
}

function startWebGL2(canvas) {
  const gl = canvas.getContext('webgl2', { alpha: false, antialias: false, powerPreference: 'low-power' });
  if (!gl) throw new Error('WebGL2 unavailable');

  const draw = (time = 0) => {
    sizeCanvas(canvas);
    gl.viewport(0, 0, canvas.width, canvas.height);
    const t = reducedMotion() ? 0 : time * 0.00022;
    gl.clearColor(
      0.025 + Math.sin(t) * 0.008,
      0.035 + Math.sin(t * 0.71 + 1.2) * 0.010,
      0.070 + Math.sin(t * 0.53 + 2.1) * 0.018,
      1,
    );
    gl.clear(gl.COLOR_BUFFER_BIT);
    if (!reducedMotion()) requestAnimationFrame(draw);
  };
  requestAnimationFrame(draw);
  return 'webgl2';
}

function startCSSFallback(canvas) {
  document.body.classList.add('appleos-css-fallback');
  canvas.style.display = 'none';
  return 'css';
}

export async function startAppleOSEffects(canvas) {
  try {
    return await startWebGPU(canvas);
  } catch {
    try {
      return startWebGL2(canvas);
    } catch {
      return startCSSFallback(canvas);
    }
  }
}
