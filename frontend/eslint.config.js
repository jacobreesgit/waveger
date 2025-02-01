import globals from "globals";
import pluginJs from "@eslint/js";
import pluginVue from "eslint-plugin-vue";
import pluginPrettier from "eslint-plugin-prettier";
import prettierConfig from "eslint-config-prettier";

/** @type {import('eslint').Linter.Config[]} */
export default [
  {
    files: ["**/*.{js,mjs,cjs,vue}"],
    languageOptions: { globals: globals.browser },
    rules: {
      // Ensures Prettier formatting issues are reported as ESLint errors
      "prettier/prettier": "error",
    },
  },
  pluginJs.configs.recommended,
  ...pluginVue.configs["flat/essential"],
  prettierConfig, // Disables conflicting ESLint rules from Prettier
  pluginPrettier.configs.recommended, // Enables Prettier as an ESLint rule
];
