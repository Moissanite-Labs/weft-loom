// Write `sample-draft.json`: a short scripted session of the instrument's own loom, for the
// Python replay test. Run from this folder:  node make_sample_draft.mjs
//
// The moves are computed here, in JavaScript, and travel in the draft as float64 bytes, so
// the replay in Python reaches the same weight roots bit for bit. On another machine or
// engine the last digits of a move can differ; the draft that results is different and
// equally valid. The committed file is one recorded session, not a conformance vector.
import fs from "node:fs";
import { Loom } from "./heddle.js";

const loom = new Loom({ seed: 7 });
const press = (treadling, shafts = {}) => {
  const d = loom.moveFor(treadling, shafts);
  const zone = loom.assess(d).zone; // the lightest gesture the zone allows
  const gesture = { auto: "release", shared: "hold", knot: "knot" }[zone];
  const result = loom.commit(d, gesture, treadling);
  if (!result.kind) throw new Error(`not recorded: ${JSON.stringify(result)}`);
  return result;
};

press({ warm: 0.08 });                          // a light touch: woven on release
loom.setPins([1056, 1057, 1120, 1121]);         // raise four heddles
press({ tilt: 0.25 });
const second = loom.fell.root;
press({ contrast: 0.2, check: 0.2 });
press({}, { 0: 0.45 });                         // too far along the stiffest shaft: this one snaps
loom.unpick(second);                            // back to the second fell
loom.setPins([]);
press({ light: -0.2 });

fs.writeFileSync(new URL("./sample-draft.json", import.meta.url), JSON.stringify(loom.exportDraft(), null, 1) + "\n");
console.log(`wrote sample-draft.json with ${loom.events.length} events; fell ${loom.fell.root.slice(0, 12)}`);
