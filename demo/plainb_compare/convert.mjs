#!/usr/bin/env node
// CLI bridge around the `plainb` npm package (the parsing core behind the
// jupyter-plainb JupyterLab extension), used to compare its output against
// Jupytext's own parsers on the same source files.
//
// Usage: node convert.mjs <parsePy|parseSphinxGallery|parseClassicMd|parseMystMd> <file>
// Prints the resulting nbformat-4 notebook as JSON on stdout.

import { register } from "node:module";
import { readFileSync } from "node:fs";

// The published `plainb` package ships compiled ESM with extension-less
// relative imports (e.g. `from "./notebook"`), which Node's ESM resolver
// rejects (bundlers normally paper over this). Register a resolve hook that
// retries with a ".js" suffix so the package loads unmodified.
register("./fix_esm_resolution.mjs", import.meta.url);

const { parsePy, parseSphinxGallery, parseClassicMd, parseMystMd } =
  await import("plainb");

const PARSERS = { parsePy, parseSphinxGallery, parseClassicMd, parseMystMd };

const [, , parserName, filePath] = process.argv;

if (!parserName || !filePath || !(parserName in PARSERS)) {
  console.error(
    `Usage: node convert.mjs <${Object.keys(PARSERS).join("|")}> <file>`,
  );
  process.exit(2);
}

const text = readFileSync(filePath, "utf-8");

try {
  const notebook = PARSERS[parserName](text);
  process.stdout.write(JSON.stringify(notebook));
} catch (err) {
  console.error(JSON.stringify({ error: String(err && err.stack || err) }));
  process.exit(1);
}
