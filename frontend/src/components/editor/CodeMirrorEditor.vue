<template>
  <div ref="containerRef" class="codemirror-host" />
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onBeforeUnmount, shallowRef } from 'vue'
import { EditorState } from '@codemirror/state'
import { EditorView, keymap, lineNumbers, highlightActiveLine, highlightActiveLineGutter, drawSelection, rectangularSelection, crosshairCursor } from '@codemirror/view'
import { defaultKeymap, history, historyKeymap, indentWithTab } from '@codemirror/commands'
import { python } from '@codemirror/lang-python'
import { oneDark } from '@codemirror/theme-one-dark'
import { syntaxHighlighting, defaultHighlightStyle, bracketMatching, foldGutter, indentOnInput } from '@codemirror/language'
import { closeBrackets, closeBracketsKeymap } from '@codemirror/autocomplete'
import { searchKeymap, highlightSelectionMatches } from '@codemirror/search'
import { lintKeymap } from '@codemirror/lint'

const props = defineProps<{
  modelValue: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

const containerRef = ref<HTMLElement | null>(null)
const view = shallowRef<EditorView | null>(null)
let ignoreChange = false

const updateListener = EditorView.updateListener.of((update) => {
  if (update.docChanged && !ignoreChange) {
    emit('update:modelValue', update.state.doc.toString())
  }
})

const theme = EditorView.theme({
  '&': { height: '100%', fontSize: '13px' },
  '.cm-scroller': { overflow: 'auto', fontFamily: '"JetBrains Mono", "Fira Code", "Cascadia Code", Consolas, monospace', lineHeight: '1.6' },
  '.cm-content': { padding: '12px 0' },
  '.cm-line': { padding: '0 12px 0 0' },
  '.cm-gutters': { minWidth: '48px', paddingRight: '4px' },
  '.cm-lineNumbers .cm-gutterElement': { padding: '0 8px 0 12px' },
  '.cm-activeLine': { backgroundColor: '#ffffff08' },
  '.cm-activeLineGutter': { backgroundColor: '#ffffff08' },
  '.cm-selectionBackground, ::selection': { backgroundColor: '#264f78 !important' },
  '.cm-cursor': { borderLeftColor: '#aeafad' },
  '.cm-matchingBracket': { backgroundColor: '#0064001a', outline: '1px solid #00640066' },
}, { dark: true })

function buildState(doc: string) {
  return EditorState.create({
    doc,
    extensions: [
      lineNumbers(),
      highlightActiveLineGutter(),
      history(),
      foldGutter(),
      drawSelection(),
      rectangularSelection(),
      crosshairCursor(),
      indentOnInput(),
      bracketMatching(),
      closeBrackets(),
      highlightActiveLine(),
      highlightSelectionMatches(),
      python(),
      oneDark,
      theme,
      keymap.of([
        indentWithTab,
        ...closeBracketsKeymap,
        ...defaultKeymap,
        ...historyKeymap,
        ...searchKeymap,
        ...lintKeymap,
      ]),
      updateListener,
    ],
  })
}

onMounted(() => {
  if (!containerRef.value) return
  view.value = new EditorView({
    state: buildState(props.modelValue),
    parent: containerRef.value,
  })
})

watch(() => props.modelValue, (newVal) => {
  if (!view.value) return
  const current = view.value.state.doc.toString()
  if (current === newVal) return
  ignoreChange = true
  view.value.dispatch({
    changes: { from: 0, to: current.length, insert: newVal },
  })
  ignoreChange = false
})

onBeforeUnmount(() => {
  view.value?.destroy()
})
</script>

<style>
.codemirror-host {
  height: 100%;
  overflow: hidden;
}
.codemirror-host .cm-editor {
  height: 100%;
  outline: none;
}
.codemirror-host .cm-editor.cm-focused {
  outline: none;
}
</style>
