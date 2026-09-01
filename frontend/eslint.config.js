// File: frontend/eslint.config.js
//
// ESLint 9 requires flat config; the project's rules are defined once here
// via FlatCompat so the legacy-style rule set (previously in .eslintrc.cjs)
// keeps working without being rewritten rule-by-rule into native flat form.
import path from "node:path";
import { fileURLToPath } from "node:url";
import { FlatCompat } from "@eslint/eslintrc";
import js from "@eslint/js";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const compat = new FlatCompat({
  baseDirectory: __dirname,
  recommendedConfig: js.configs.recommended,
});

export default [
  { ignores: ["dist/**", "node_modules/**"] },
  ...compat
    .config({
      root: true,
      env: { browser: true, es2022: true, node: true },
      extends: [
        "eslint:recommended",
        "plugin:@typescript-eslint/recommended",
        "plugin:react-hooks/recommended",
      ],
      parser: "@typescript-eslint/parser",
      plugins: ["react-refresh"],
      rules: {
        "react-refresh/only-export-components": ["warn", { allowConstantExport: true }],
        "@typescript-eslint/no-unused-vars": ["error", { argsIgnorePattern: "^_" }],
      },
    })
    .map((config) => ({ ...config, files: ["**/*.{ts,tsx}"] })),
];
