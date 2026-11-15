import fs from "node:fs";
import path from "node:path";
import { pathToFileURL } from "node:url";
const _wi = process.argv.indexOf("--weft");
const _weft = (_wi > 0 && _wi + 1 < process.argv.length) ? process.argv[_wi + 1] : process.env.WEFT_CHECKOUT;
if (!_weft) { console.error("give the weft software checkout with --weft PATH or the WEFT_CHECKOUT environment variable"); process.exit(2); }
const { verifyWeightUpdateSafety } = await import(pathToFileURL(path.resolve(_weft, "site/assets/js/invariant-gate.js")).href);
const S={Inf:Infinity,"-Inf":-Infinity,NaN:NaN}; const dec=x=>(typeof x==="string"&&x in S)?S[x]:x;
const enc=x=>Number.isNaN(x)?"NaN":x===Infinity?"Inf":x===-Infinity?"-Inf":x;
const out=[];
for(const line of fs.readFileSync(process.argv[2],"utf8").split("\n")){ if(!line)continue; const c=JSON.parse(line);
  if(c.mask!==null){out.push(JSON.stringify({id:c.id,skip:"no_mask_support"}));continue;}
  const g=verifyWeightUpdateSafety(c.base.map(dec),c.cand.map(dec),dec(c.r),dec(c.b),dec(c.c));
  out.push(JSON.stringify({id:c.id,acc:g.accepted,dist:enc(g.distance),rem:enc(g.remainingBudget),reason:g.reason}));}
fs.writeFileSync(process.argv[3],out.join("\n")+"\n");
