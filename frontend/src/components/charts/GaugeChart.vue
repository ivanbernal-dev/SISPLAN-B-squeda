<template>
  <div
    class="relative flex items-center justify-center"
    :style="{ width: sizeMap[size].container, height: sizeMap[size].container }"
    ref="chartEl"
    role="img"
    :aria-label="`${title}: ${value}%`"
  />
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import * as echarts from 'echarts/core'
import { GaugeChart as EGaugeChart } from 'echarts/charts'
import { CanvasRenderer } from 'echarts/renderers'

echarts.use([EGaugeChart, CanvasRenderer])

interface Props {
  value: number
  title?: string
  subtitle?: string
  size?: 'sm' | 'md' | 'lg'
  color?: string
}

const props = withDefaults(defineProps<Props>(), {
  size: 'md',
  color: '#3e9c45',
})

const emit = defineEmits<{ click: [value: number] }>()

const chartEl = ref<HTMLElement | null>(null)
let chart: echarts.ECharts | null = null

const sizeMap = {
  sm: { container: '160px', fontSize: 20, trackWidth: 14 },
  md: { container: '200px', fontSize: 28, trackWidth: 18 },
  lg: { container: '260px', fontSize: 36, trackWidth: 22 },
}

function buildOption() {
  const s = sizeMap[props.size]
  return {
    backgroundColor: 'transparent',
    series: [
      {
        type: 'gauge',
        startAngle: 180,
        endAngle: 0,
        min: 0,
        max: 100,
        radius: '90%',
        center: ['50%', '70%'],
        animationDuration: 1200,
        animationEasing: 'cubicOut',
        progress: {
          show: true,
          roundCap: true,
          width: s.trackWidth,
          itemStyle: { color: props.color },
        },
        axisLine: {
          roundCap: true,
          lineStyle: {
            width: s.trackWidth,
            color: [[1, '#E8EDF0']],
          },
        },
        pointer: { show: false },
        axisTick: { show: false },
        splitLine: { show: false },
        axisLabel: { show: false },
        title: { show: false },
        detail: {
          show: true,
          offsetCenter: [0, '-15%'],
          formatter: (val: number) => `${val.toLocaleString('es-CO', { maximumFractionDigits: 1 })}%`,
          fontFamily: 'Barlow, sans-serif',
          fontSize: s.fontSize,
          fontWeight: 700,
          color: '#2D3748',
        },
        data: [{ value: props.value }],
      },
    ],
  }
}

function initChart() {
  if (!chartEl.value) return
  chart = echarts.init(chartEl.value, null, { renderer: 'canvas' })
  chart.setOption(buildOption())
  chart.on('click', () => emit('click', props.value))
}

const resizeHandler = () => chart?.resize()

onMounted(() => {
  initChart()
  window.addEventListener('resize', resizeHandler)
})

onUnmounted(() => {
  chart?.dispose()
  window.removeEventListener('resize', resizeHandler)
})

watch(() => [props.value, props.color, props.size], () => {
  chart?.setOption(buildOption(), { notMerge: false })
})
</script>
