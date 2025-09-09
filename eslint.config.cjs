// Flat ESLint config (migrated from .eslintrc.cjs)
// Scoped to React + TypeScript project source; ignores build & legacy static JS blobs.

import js from '@eslint/js'
import ts from '@typescript-eslint/eslint-plugin'
import tsParser from '@typescript-eslint/parser'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'
import importPlugin from 'eslint-plugin-import'
import unusedImports from 'eslint-plugin-unused-imports'
import promise from 'eslint-plugin-promise'

export default [
  {
    ignores: [
      'dist/**',
      'build/**',
      'coverage/**',
      'node_modules/**',
      'src/assets/html/assets/js/**'
    ]
  },
  {
  files: ['src/**/*.ts', 'src/**/*.tsx'],
    languageOptions: {
      parser: tsParser,
      parserOptions: { ecmaVersion: 'latest', sourceType: 'module' },
      globals: { ...js.configs.recommended.languageOptions?.globals }
    },
    plugins: {
      '@typescript-eslint': ts,
      'react-hooks': reactHooks,
      'react-refresh': reactRefresh,
      import: importPlugin,
      'unused-imports': unusedImports,
      promise
    },
    rules: {
      ...js.configs.recommended.rules,
      ...ts.configs.recommended.rules,
      'react-refresh/only-export-components': ['warn', { allowConstantExport: true }],
      '@typescript-eslint/no-unused-vars': ['warn', { argsIgnorePattern: '^_', varsIgnorePattern: '^_', ignoreRestSiblings: true }],
      '@typescript-eslint/no-explicit-any': ['warn', { ignoreRestArgs: true }],
      '@typescript-eslint/ban-types': ['warn', { extendDefaults: true }],
      '@typescript-eslint/consistent-type-imports': ['warn', { prefer: 'type-imports', disallowTypeAnnotations: false }],
      'unused-imports/no-unused-imports': 'warn',
      'import/order': ['warn', {
        groups: ['builtin', 'external', 'internal', 'parent', 'sibling', 'index', 'object', 'type'],
        'newlines-between': 'always',
        alphabetize: { order: 'asc', caseInsensitive: true }
      }],
      'promise/no-new-statics': 'error',
      'promise/no-return-wrap': 'error',
      'promise/no-multiple-resolved': 'warn',
      'no-duplicate-case': 'error',
      'eqeqeq': ['warn', 'smart'],
      'prefer-const': ['warn', { destructuring: 'all' }],
      'react-hooks/exhaustive-deps': 'warn',
      'no-restricted-imports': ['warn', {
        patterns: [
          { group: ['../components/*', '../../components/*', './components/*'], message: 'Use feature slice alias (@features/...) or refactor.' },
          { group: ['../pages/*', '../../pages/*'], message: 'Pages route through App or migrate to feature slices.' }
        ]
      }]
    }
  }
]
