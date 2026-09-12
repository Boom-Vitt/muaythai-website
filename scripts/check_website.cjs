// Run from the project root: node scripts/check_website.cjs (Node + FFprobe)
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { execFileSync } = require('node:child_process');
const root = path.resolve(__dirname, '..');
const html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
const scripts = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(match => match[1]);
assert.equal(scripts.length, 1);
new Function(scripts[0]);
const hero = html.match(/<section class="hero"[\s\S]*?<\/section>/)[0];
assert.ok(hero.includes('h3-cinematic-bg.mp4') && hero.includes('akhani-cinematic-poster.jpg'));
assert.ok(!hero.includes('<model-viewer'), 'Cinematic hero stays separate from the interactive fight lab');
for (const [, asset] of html.matchAll(/(?:src|href|poster)="(web-assets\/[^"#]+)"/g)) {
  assert.ok(fs.statSync(path.join(root, asset)).size > 0, `Missing asset: ${asset}`);
}
const ids = [...html.matchAll(/\bid="([^"]+)"/g)].map(match => match[1]);
assert.equal(ids.length, new Set(ids).size, 'HTML IDs must be unique');
for (const [, target] of html.matchAll(/(?:href="#|aria-controls=")([^" ]+)"/g)) {
  assert.ok(ids.includes(target), `Missing anchor/control: ${target}`);
}
const glb = fs.readFileSync(path.join(root, 'web-assets/akhani-combat.glb'));
const gltf = JSON.parse(glb.toString('utf8', 20, 20 + glb.readUInt32LE(12)));
const animation = gltf.animations.find(animation => animation.name === 'Combat_Combo');
assert.ok(animation?.channels.length > 10, 'Ship the actual multi-bone Combat_Combo animation');
assert.ok(animation.samplers.every(sampler => Math.abs(gltf.accessors[sampler.input].min[0]) < 1e-6), 'Animation starts at video time zero');
assert.ok(Math.abs(Math.max(...animation.samplers.map(sampler => gltf.accessors[sampler.input].max[0])) - 10) < 1e-6, 'Combo duration matches the ten-second film');

function probeMedia(file) {
  return JSON.parse(execFileSync('ffprobe', ['-v', 'error', '-show_entries', 'stream=codec_type,width,height,duration,nb_frames,avg_frame_rate', '-of', 'json', path.join(root, 'web-assets', file)], { encoding: 'utf8' }));
}
const probe = probeMedia('combat-preview.mp4');
assert.equal(probe.streams[0].nb_frames, '300', 'Render must contain all 300 final combo frames');
assert.equal(probe.streams[0].avg_frame_rate, '30/1');
assert.ok(Math.abs(Number(probe.streams[0].duration) - 10) < 1e-6, 'Render and model use the same ten-second clock');
const cinematic = probeMedia('h3-cinematic-bg.mp4');
assert.deepEqual(cinematic.streams.map(stream => [stream.codec_type, stream.width, stream.height, stream.avg_frame_rate, Number(stream.nb_frames), Number(stream.duration)]),
  [['video', 1024, 576, '24/1', 240, 10]], 'Final cinematic must be 1024×576, 24 fps, 240 frames / 10 seconds, with no audio');

// Exercise the actual page script, not duplicated playback logic, with browser media events.
function page(reducedMotion = false) {
  const queue = [];
  class Element {
    constructor() { this.listeners = {}; this.attributes = {}; this.parts = {}; this.dataset = {}; this.style = {}; this.textContent = ''; this.disabled = false; this.open = false; }
    addEventListener(type, callback) { (this.listeners[type] ??= []).push(callback); }
    emit(type) { for (const callback of this.listeners[type] ?? []) callback({ target: this }); }
    setAttribute(name, value) { this.attributes[name] = value; }
    getAttribute(name) { return this.attributes[name]; }
    querySelector(selector) { return this.parts[selector] ??= new Element(); }
    querySelectorAll() { return []; }
    getClientRects() { return [1]; }
    focus() {}
    showModal() { this.open = true; }
    close() { this.open = false; this.emit('close'); }
    classList = { remove() {}, contains() { return false; }, toggle() { return true; } };
  }
  class Media extends Element {
    paused = true; currentTime = 0; readyState = 4; duration = 10; playbackRate = 1;
    play() { if (this.paused) { this.paused = false; queue.push(() => this.emit('play')); } return Promise.resolve(); }
    pause() { if (!this.paused) { this.paused = true; queue.push(() => this.emit('pause')); } }
    load() {}
  }
  const elements = Object.fromEntries(ids.map(id => [id, new Element()]));
  for (const id of ['background-video', 'rhythm-video', 'film-video']) elements[id] = new Media();
  const model = elements['fighter-model'];
  Object.assign(model, { paused: true, currentTime: 0, duration: 10, availableAnimations: ['Combat_Combo'], play() { this.paused = false; }, pause() { this.paused = true; }, resetTurntableRotation() {}, jumpCameraToGoal() {} });
  const beats = [...html.matchAll(/class="beat-button" data-time="([^"]+)"/g)].map(([, time]) => {
    const button = new Element(); button.dataset.time = time; return button;
  });
  const watch = new Element();
  const preference = new Element(); preference.matches = reducedMotion;
  const document = new Element();
  document.hidden = false;
  document.body = new Element();
  document.querySelector = selector => elements[selector.slice(1)];
  document.querySelectorAll = selector => selector === '[data-time]' ? beats : [watch];
  vm.runInNewContext(scripts[0], { document, window: { matchMedia: () => preference }, requestAnimationFrame: () => 1, cancelAnimationFrame() {} });
  function flush() { let count = 0; while (queue.length) { assert.ok(++count < 30, 'Media event loop must settle'); queue.shift()(); } }
  model.emit('load'); flush();
  return { elements, model, video: elements['rhythm-video'], beats, document, preference, watch, flush };
}
const p = page();
assert.equal(p.model.paused, false, 'Combat starts when motion is permitted');
for (const button of p.beats) {
  button.emit('click'); p.flush();
  assert.equal(p.model.paused, true);
  assert.equal(p.video.paused, true);
  assert.ok(Math.abs(p.model.currentTime - Number(button.dataset.time)) < 1e-6);
  assert.equal(p.video.currentTime, p.model.currentTime, 'Beat button seeks both real media clocks');
  assert.equal(button.getAttribute('aria-pressed'), 'true');
}
p.elements['combo-replay'].emit('click');
p.elements['combo-toggle'].emit('click'); p.flush();
assert.equal(p.model.paused, true, 'Queued video play cannot undo a newer user pause');
p.elements['combo-replay'].emit('click'); p.flush();
assert.equal(p.model.currentTime, 0); assert.equal(p.video.currentTime, 0);
assert.equal(p.model.paused, false); assert.equal(p.video.paused, false);
p.document.hidden = true; p.document.emit('visibilitychange'); p.flush();
assert.equal(p.model.paused, true); assert.equal(p.video.paused, true);
p.document.hidden = false; p.document.emit('visibilitychange'); p.flush();
assert.equal(p.model.paused, false, 'Return restores prior playing state');
p.video.currentTime = 3.1333333333; p.video.emit('seeked');
assert.equal(p.model.currentTime, p.video.currentTime, 'Native scrub controls the model pose');
p.video.pause(); p.flush(); assert.equal(p.model.paused, true);
p.watch.emit('click'); p.flush();
assert.equal(p.elements['film-video'].src, 'web-assets/h3-cinematic-bg.mp4', 'Watch opens the final cinematic film');
p.elements['film-dialog'].close(); p.flush();
assert.equal(p.model.paused, true, 'Closing film must preserve an explicitly paused combo');
p.elements['combo-toggle'].emit('click'); p.flush();
assert.equal(p.model.paused, false);
p.preference.matches = true; p.preference.emit('change'); p.flush();
assert.equal(p.model.paused, true); assert.equal(p.video.paused, true);
const originalBackground = p.elements['background-video'].src;
p.elements['background-video'].emit('error');
assert.equal(p.elements['background-video'].src, originalBackground, 'Failed cinematic media must not substitute the motion-reference model');
assert.equal(p.elements['background-video'].style.visibility, 'hidden');
const reduced = page(true);
assert.equal(reduced.model.paused, true); assert.equal(reduced.video.paused, true);
assert.equal(reduced.elements['background-video'].paused, true);
console.log('Passed: shipped assets/Combat_Combo, syntax, IDs, all six pose seeks, replay, native scrubbing, pause preservation, visibility and reduced motion.');
