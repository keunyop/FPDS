import path from "node:path";
import { readFileSync, existsSync } from "node:fs";
import { createRequire } from "node:module";
import vm from "node:vm";
import React from "react";
import ts from "typescript";

const cache = new Map();
const sourceRoot = path.resolve(import.meta.dirname, "../src");

// Server-render real local components; only Next routing needs a test boundary.
export function loadComponent(relativePath) {
  const filename = path.resolve(sourceRoot, relativePath);
  if (cache.has(filename)) return cache.get(filename).exports;
  const module = { exports: {} };
  cache.set(filename, module);
  const nativeRequire = createRequire(filename);
  const require = (id) => {
    if (id === "next/navigation") return {useRouter: () => ({refresh() {}, push() {}, replace() {}})};
    if (id === "next/link") return {__esModule: true, default: React.forwardRef(function Link({href, ...props}, ref) {
      return React.createElement("a", {...props, href, ref});
    })};
    if (id.startsWith("@/") || id.startsWith(".")) {
      const base = id.startsWith("@/") ? path.join(sourceRoot, id.slice(2)) : path.resolve(path.dirname(filename), id);
      const local = [base, base + ".tsx", base + ".ts"].find(candidate => existsSync(candidate));
      if (local?.match(/\.tsx?$/)) return loadComponent(path.relative(sourceRoot, local));
    }
    return nativeRequire(id);
  };
  const compiled = ts.transpileModule(readFileSync(filename, "utf8"), {
    compilerOptions: {module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.ReactJSX, target: ts.ScriptTarget.ES2022, esModuleInterop: true},
    fileName: filename,
  }).outputText;
  const execute = new vm.Script(`(function(require, module, exports) {${compiled}\n})`, {filename}).runInThisContext();
  execute(require, module, module.exports);
  return module.exports;
}
