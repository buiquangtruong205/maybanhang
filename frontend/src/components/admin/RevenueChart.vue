<template>
  <div class="chart-container">
    <div class="chart-header">
      <h3>Doanh thu</h3>
      <div class="period-selector">
        <button 
          v-for="p in ['week', 'month']" 
          :key="p"
          @click="$emit('period-change', p)"
          :class="{ active: period === p }"
        >
          {{ p === 'week' ? '7 ngày' : '30 ngày' }}
        </button>
      </div>
    </div>
    <div class="canvas-wrapper">
      <Line v-if="chartData.labels" :data="chartData" :options="chartOptions" />
      <div v-else class="loading">Đang tải biểu đồ...</div>
    </div>
  </div>
</template>

<script setup>
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js'
import { Line } from 'vue-chartjs'
import { computed } from 'vue'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
)

const props = defineProps({
  period: String,
  data: Object
})

defineEmits(['period-change'])

const chartData = computed(() => ({
  labels: props.data?.labels || [],
  datasets: [
    {
      label: 'Doanh thu (VNĐ)',
      backgroundColor: (ctx) => {
        const canvas = ctx.chart.ctx
        const gradient = canvas.createLinearGradient(0, 0, 0, 400)
        gradient.addColorStop(0, 'rgba(16, 185, 129, 0.4)')
        gradient.addColorStop(1, 'rgba(16, 185, 129, 0)')
        return gradient
      },
      borderColor: '#10B981',
      borderWidth: 2,
      pointBackgroundColor: '#10B981',
      pointBorderColor: '#fff',
      pointHoverBackgroundColor: '#fff',
      pointHoverBorderColor: '#10B981',
      fill: true,
      tension: 0.4,
      data: props.data?.data || []
    }
  ]
}))

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false },
    tooltip: {
      mode: 'index',
      intersect: false,
      backgroundColor: 'rgba(0, 0, 0, 0.8)',
      titleColor: '#fff',
      bodyColor: '#fff',
      borderColor: 'rgba(255, 255, 255, 0.1)',
      borderWidth: 1,
      padding: 10,
      displayColors: false,
      callbacks: {
        label: (context) => new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(context.raw)
      }
    }
  },
  scales: {
    x: {
      grid: { display: false, drawBorder: false },
      ticks: { color: 'rgba(255, 255, 255, 0.5)' }
    },
    y: {
      grid: { color: 'rgba(255, 255, 255, 0.05)', drawBorder: false },
      ticks: { color: 'rgba(255, 255, 255, 0.5)', callback: (value) => value >= 1000 ? `${value/1000}k` : value },
      beginAtZero: true
    }
  },
  interaction: {
    mode: 'nearest',
    axis: 'x',
    intersect: false
  }
}
</script>

<style scoped>
.chart-container {
  background: var(--color-card);
  border: 1px solid rgba(255,255,255,0.05);
  border-radius: 1rem;
  padding: 1.5rem;
  height: 100%;
  display: flex; flex-direction: column;
}
.chart-header {
  display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;
}
.chart-header h3 { color: white; margin: 0; font-size: 1.125rem; }
.period-selector {
  display: flex; gap: 0.5rem; background: rgba(255,255,255,0.05); padding: 0.25rem; border-radius: 0.5rem;
}
.period-selector button {
  background: transparent; border: none; color: rgba(255,255,255,0.5); padding: 0.25rem 0.75rem; border-radius: 0.375rem; cursor: pointer; font-size: 0.875rem; transition: all 0.2s;
}
.period-selector button.active {
  background: var(--color-primary); color: white;
}
.period-selector button:hover:not(.active) {
  color: white;
}
.canvas-wrapper {
  flex: 1; min-height: 250px; position: relative;
}
.loading {
  position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; color: rgba(255,255,255,0.3);
}
</style>
