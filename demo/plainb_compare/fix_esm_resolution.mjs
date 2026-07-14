// The published `plainb` package ships compiled ESM with extension-less
// relative imports (e.g. `from "./notebook"`), which bundlers resolve
// automatically but Node's own ESM resolver rejects. This loader hook
// retries a failed relative-specifier resolution with a ".js" suffix,
// which is enough to load the package unmodified from node_modules.
export async function resolve(specifier, context, nextResolve) {
  try {
    return await nextResolve(specifier);
  } catch (err) {
    if (err?.code === "ERR_MODULE_NOT_FOUND" && specifier.startsWith(".")) {
      return nextResolve(specifier + ".js");
    }
    throw err;
  }
}
