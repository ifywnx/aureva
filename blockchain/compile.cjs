const fs = require('node:fs');
const solc = require('solc');
const input={language:'Solidity',sources:{'AurevaRegistry.sol':{content:fs.readFileSync('AurevaRegistry.sol','utf8')}},settings:{optimizer:{enabled:true,runs:200},evmVersion:'paris',outputSelection:{'*':{'*':['abi','evm.bytecode.object']}}}};
const out=JSON.parse(solc.compile(JSON.stringify(input)));
for(const e of out.errors||[]) { console.error(e.formattedMessage); if(e.severity==='error') process.exit(1); }
const c=out.contracts['AurevaRegistry.sol'].AurevaRegistry;
fs.writeFileSync('artifact.json',JSON.stringify({abi:c.abi,bytecode:'0x'+c.evm.bytecode.object},null,2));
console.log('AurevaRegistry compiled');
