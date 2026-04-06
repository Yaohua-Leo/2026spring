#!/usr/bin/env node
const path = require("path");

if (typeof process.stdout.clearLine !== "function") {
  process.stdout.clearLine = () => {};
}
if (typeof process.stdout.cursorTo !== "function") {
  process.stdout.cursorTo = () => {};
}

const cliPath = path.join(
  process.env.APPDATA || path.join(process.env.USERPROFILE || "", "AppData", "Roaming"),
  "npm",
  "node_modules",
  "@mathpix",
  "mpx-cli",
  "bin",
  "cli.js"
);

require(cliPath);
