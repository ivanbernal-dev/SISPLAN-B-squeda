module.exports = {
  root: true,
  env: {
    browser: true,
    es2022: true,
    node: true,
  },
  parser: 'vue-eslint-parser',
  parserOptions: {
    parser: '@typescript-eslint/parser',
    ecmaVersion: 'latest',
    sourceType: 'module',
  },
  plugins: ['@typescript-eslint'],
  extends: ['plugin:vue/vue3-essential'],
  rules: {
    'vue/multi-word-component-names': 'off',
  },
  ignorePatterns: ['dist/', 'node_modules/'],
}
