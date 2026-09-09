// Run from the project root: node scripts/check_website.cjs
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
const scripts = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(match => match[1]);
assert.equal(scripts.length, 1);
new Function(scripts[0]); // Parse the actual shipped JavaScript.

for (const [, asset] of html.matchAll(/(?:src|href|poster)="(web-assets\/[^"#]+)"/g)) {
  assert.ok(fs.statSync(path.join(root, asset)).size > 0, `Missing asset: ${asset}`);
}
const ids = [...html.matchAll(/\bid="([^"]+)"/g)].map(match => match[1]);
assert.equal(ids.length, new Set(ids).size, 'HTML IDs must be unique');
for (const [, target] of html.matchAll(/(?:href="#|aria-controls=")([^" ]+)"/g)) {
  assert.ok(ids.includes(target), `Missing anchor/control: ${target}`);
}

// Exercise the production beat-selection function at actual frame boundaries.
const states = [];
const buttons = [0, 1, 2].map(index => ({ setAttribute: (_, value) => { states[index] = value; } }));
const selectionSource = scripts[0].match(/function highlightBeat\(time\) \{[\s\S]*?\n    \}/)[0];
const selectBeat = new Function('beatButtons', `${selectionSource}; return highlightBeat;`)(buttons);
for (const [time, active] of [[0, 0], [1.624, 0], [1.625, 1], [3.957, 1], [3.958, 2], [5.999, 2]]) {
  selectBeat(time);
  assert.deepEqual(states, buttons.map((_, index) => String(index === active)), `Beat at ${time}s`);
}
const motionSource = scripts[0].match(/function syncModelMotion\(\) \{[\s\S]*?\n    \}/)[0];
for (const [wanted, hidden, dialogOpen, expectedPlay] of [
  [true, false, false, true], [false, false, false, false],
  [true, true, false, false], [true, false, true, false],
]) {
  const fighter = { availableAnimations: ['Guard_Idle'], paused: true,
    play() { this.paused = false; }, pause() { this.paused = true; } };
  const syncMotion = new Function('modelReady', 'wantsBackgroundMotion', 'document', 'dialog', 'model', 'updateBackgroundControl', `${motionSource}; return syncModelMotion;`)(true, wanted, { hidden }, { open: dialogOpen }, fighter, () => {});
  syncMotion();
  assert.equal(!fighter.paused, expectedPlay, 'Idle playback must respect user pause, visibility and modal');
}
console.log('Website checks passed: JavaScript syntax, local assets, unique IDs, anchors, six beat boundaries, four motion states.');
