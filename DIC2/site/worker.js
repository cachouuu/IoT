'use strict';
importScripts('engine.js');
onmessage=event=>{try{const {parsed,target,name}=event.data;const result=DIC2_ENGINE.analyze(parsed,target,name);postMessage({result});}catch(error){postMessage({error:error.message});}};
