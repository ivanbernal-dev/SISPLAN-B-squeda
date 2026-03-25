import type { Directive } from 'vue'

function fit(el: HTMLTextAreaElement) {
  el.style.height = 'auto'
  el.style.height = `${el.scrollHeight}px`
}

export const vAutoresize: Directive<HTMLTextAreaElement> = {
  mounted(el) {
    el.style.overflowY = 'hidden'
    el.style.resize = 'none'
    fit(el)
    el.addEventListener('input', () => fit(el))
  },
  updated(el) {
    fit(el)
  },
}
