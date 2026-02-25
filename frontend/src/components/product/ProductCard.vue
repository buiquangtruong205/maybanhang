<template>
  <!-- Card Sản phẩm: Hiển thị thông tin cơ bản và hình ảnh -->
  <div 
    class="product-card group relative bg-white rounded-2xl shadow-md overflow-hidden cursor-pointer transition-all duration-300 hover:shadow-xl hover:-translate-y-1 active:scale-[0.98]"
    :class="{ 'opacity-60 grayscale-[0.5]': product.stock <= 0 }"
    @click="$emit('select', product)"
  >
    <!-- Hình ảnh sản phẩm kèm overlay khi hết hàng -->
    <div class="product-image relative aspect-square bg-slate-100 overflow-hidden">
      <img 
        :src="product.image_url" 
        :alt="product.name" 
        class="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
        @error="handleImageError"
        loading="lazy"
      />
      
      <!-- Overlay khi hết hàng -->
      <div v-if="product.stock <= 0" class="absolute inset-0 bg-black/40 backdrop-blur-[2px] flex items-center justify-center">
        <span class="bg-white/90 text-black px-4 py-1 rounded-full font-bold text-sm uppercase tracking-wider">Hết hàng</span>
      </div>
      
      <!-- Danh mục sản phẩm (Badge góc trái) -->
      <span class="absolute top-3 left-3 bg-black/30 backdrop-blur-md text-white text-[10px] uppercase font-bold px-2 py-0.5 rounded-md border border-white/20">
        {{ product.category }}
      </span>
    </div>

    <!-- Thông tin chi tiết sản phẩm -->
    <div class="p-4">
      <h3 class="font-bold text-slate-800 text-base leading-tight mb-1 truncate group-hover:text-primary transition-colors">
        {{ product.name }}
      </h3>
      <p class="text-xs text-slate-500 line-clamp-2 mb-3 h-8 leading-relaxed">
        {{ product.description }}
      </p>
      
      <!-- Hàng dưới cùng: Giá và Tồn kho -->
      <div class="flex items-center justify-between mt-auto pt-2 border-t border-slate-50">
        <span class="text-lg font-black text-rose-600">
          {{ formatPrice(product.price) }}
        </span>
        <span 
          v-if="product.stock > 0" 
          class="text-[10px] font-bold px-2 py-0.5 rounded-full"
          :class="product.stock < 5 ? 'bg-amber-50 text-amber-600' : 'bg-emerald-50 text-emerald-600'"
        >
          Còn {{ product.stock }}
        </span>
        <span v-else class="text-[10px] font-bold px-2 py-0.5 rounded-full bg-slate-100 text-slate-400">
          Tạm hết
        </span>
      </div>
    </div>
  </div>
</template>

<script setup>
/**
 * ProductCard Component
 * Hiển thị thẻ thông tin sản phẩm dành cho giao diện Kiosk/Mobile.
 */
defineProps({
  product: {
    type: Object,
    required: true
  }
})

defineEmits(['select'])

// Định dạng tiền tệ VND
function formatPrice(p) {
  return new Intl.NumberFormat('vi-VN', { 
    style: 'currency', 
    currency: 'VND' 
  }).format(p)
}

// Xử lý khi ảnh bị lỗi không tải được
function handleImageError(e) {
  e.target.src = '/images/default-product.png'
}
</script>

<style scoped>
.product-card {
  /* Animation xuất hiện từ từ */
  animation: fadeInUp 0.4s ease-out both;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(12px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
