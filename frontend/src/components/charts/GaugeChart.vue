<template>
  <div
    :style="{ width: sizeMap[size].width, height: sizeMap[size].height }"
    ref="chartEl"
    class="cursor-pointer"
    @click="emit('click', props.value)"
    role="img"
    :aria-label="`${title}: ${value}% de completitud`"
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
  title: string
  subtitle?: string
  size?: 'sm' | 'md' | 'lg'
  variant?: 'primary' | 'secondary'
}

const props = withDefaults(defineProps<Props>(), {
  size: 'md',
  variant: 'primary',
})

const emit = defineEmits<{
  click: [value: number]
}>()

const chartEl = ref<HTMLElement | null>(null)
let chart: echarts.ECharts | null = null

const sizeMap = {
  sm: { width: '180px', height: '160px' },
  md: { width: '240px', height: '210px' },
  lg: { width: '320px', height: '280px' },
}

const colorScales = {
  primary: [
    [0.3, '#FF6900'],
    [0.7, '#A97CC9'],
    [1, '#52ABAB'],
  ] as [number, string][],
  secondary: [
    [0.4, '#FF6900'],
    [0.75, '#3E818F'],
    [1, '#52ABAB'],
  ] as [number, string][],
}

function buildOption() {
  const colors = colorScales[props.variant]
  const subtitleText = props.subtitle ? `\n${props.subtitle}` : ''

  return {
    backgroundColor: '#FFFFFF',
    series: [
      {
        type: 'gauge',
        startAngle: 200,
        endAngle: -20,
        min: 0,
        max: 100,
        splitNumber: 5,
        animationDuration: 1500,
        animationEasing: 'cubicOut',
        axisLine: {
          lineStyle: {
            width: props.size === 'sm' ? 12 : props.size === 'lg' ? 22 : 16,
            color: colors,
          },
        },
        pointer: {
          show: true,
          length: '65%',
          width: props.size === 'sm' ? 4 : 6,
          itemStyle: {
            color: '#323232',
          },
        },
        axisTick: {
          show: false,
        },
        splitLine: {
          show: false,
        },
        axisLabel: {
          show: false,
        },
        title: {
          show: true,
          offsetCenter: [0, '75%'],
          fontFamily: 'Montserrat, sans-serif',
          fontSize: props.size === 'sm' ? 10 : props.size === 'lg' ? 14 : 12,
          fontWeight: 600,
          color: '#323232',
          overflow: 'truncate',
          width: props.size === 'sm' ? 140 : props.size === 'lg' ? 260 : 190,
        },
        detail: {
          show: true,
          offsetCenter: [0, '35%'],
          formatter: '{value}%',
          fontFamily: 'Barlow, sans-serif',
          fontSize: props.size === 'sm' ? 18 : props.size === 'lg' ? 28 : 22,
          fontWeight: 700,
          color: '#323232',
        },
        data: [
          {
            value: Math.round(props.value),
            name: props.title + subtitleText,
          },
        ],
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

function updateChart() {
  chart?.setOption(buildOption(), { notMerge: false })
}

onMounted(() => {
  initChart()
  window.addEventListener('resize', () => chart?.resize())
})

onUnmounted(() => {
  chart?.dispose()
  window.removeEventListener('resize', () => chart?.resize())
})

watch(() => [props.value, props.title, props.subtitle, props.variant], updateChart)
</script>
