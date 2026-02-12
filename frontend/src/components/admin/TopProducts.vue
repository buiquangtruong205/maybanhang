<template>
  <div class="top-products-card">
    <h3>Sản phẩm bán chạy</h3>
    <div class="table-wrapper">
      <table v-if="products.length">
        <thead>
          <tr>
            <th>Tên sản phẩm</th>
            <th class="text-right">Đã bán</th>
            <th class="text-right">Doanh thu</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(p, i) in products" :key="i">
            <td>
              <div class="product-info">
                <span class="rank" :class="`rank-${i+1}`">{{ i + 1 }}</span>
                <span class="name">{{ p.name }}</span>
              </div>
            </td>
            <td class="text-right count">{{ p.sold }}</td>
            <td class="text-right revenue">{{ formatVnd(p.revenue) }}</td>
          </tr>
        </tbody>
      </table>
      <div v-else class="empty">Chưa có dữ liệu bán hàng</div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  products: Array
})

function formatVnd(v) {
  return new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(v)
}
</script>

<style scoped>
.top-products-card {
  background: var(--color-card);
  border: 1px solid rgba(255,255,255,0.05);
  border-radius: 1rem;
  padding: 1.5rem;
  height: 100%;
}
h3 { color: white; margin: 0 0 1rem 0; font-size: 1.125rem; }
.table-wrapper { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; }
th { text-align: left; color: rgba(255,255,255,0.4); font-size: 0.75rem; text-transform: uppercase; padding-bottom: 0.75rem; font-weight: 600; }
td { padding: 0.75rem 0; border-bottom: 1px solid rgba(255,255,255,0.05); color: rgba(255,255,255,0.9); font-size: 0.9375rem; }
tr:last-child td { border-bottom: none; }
.text-right { text-align: right; }
.product-info { display: flex; align-items: center; gap: 0.75rem; }
.rank {
  width: 24px; height: 24px; display: flex; align-items: center; justify-content: center;
  border-radius: 50%; background: rgba(255,255,255,0.1); font-size: 0.75rem; font-weight: 700; color: white;
}
.rank-1 { background: #FFD700; color: black; }
.rank-2 { background: #C0C0C0; color: black; }
.rank-3 { background: #CD7F32; color: black; }
.name { font-weight: 500; }
.revenue { font-family: 'Rubik', sans-serif; color: var(--color-success); }
.empty { text-align: center; color: rgba(255,255,255,0.3); padding: 2rem; }
</style>
