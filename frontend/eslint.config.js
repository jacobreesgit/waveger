import globals from 'globals'
import pluginJs from '@eslint/js'
import pluginVue from 'eslint-plugin-vue'
import pluginPrettier from 'eslint-plugin-prettier'
import pluginTs from '@typescript-eslint/eslint-plugin'
import parserTs from '@typescript-eslint/parser'
import prettierConfig from 'eslint-config-prettier'

/** @type {import('eslint').Linter.FlatConfig[]} */
export default [
  {
    files: ['**/*.{js,mjs,cjs,ts,tsx,vue}'], // Added TS & TSX files
    languageOptions: {
      globals: globals.browser,
      parser: parserTs,
      parserOptions: {
        sourceType: 'module',
        project: './tsconfig.json',
      },
    },
    rules: {
      'prettier/prettier': 'error',
    },
  },
  pluginJs.configs.recommended,
  pluginTs.configs.recommended, // Enables recommended TypeScript rules
  ...pluginVue.configs['flat/essential'],
  prettierConfig, // Disables conflicting ESLint rules from Prettier
  pluginPrettier.configs.recommended, // Enables Prettier as an ESLint rule
]
