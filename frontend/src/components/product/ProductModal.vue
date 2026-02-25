<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="product" class="modal-overlay">
        <!-- Lớp nền mờ để tập trung vào Modal -->
        <div class="modal-backdrop" @click="$emit('close')" />
        
        <!-- Nội dung Modal -->
        <div class="product-modal shadow-2xl animate-scale-in">
          <!-- Phần đầu: Hình ảnh lớn với hiệu ứng Gradient -->
          <div class="modal-hero relative h-56 bg-white overflow-hidden">
            <img :src="product.image_url" :alt="product.name" class="w-full h-full object-cover" />
            <div class="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent" />
            
            <!-- Nút đóng Modal -->
            <button @click="$emit('close')" class="absolute top-4 right-4 w-10 h-10 bg-black/20 hover:bg-black/40 backdrop-blur-md rounded-full text-white flex items-center justify-center transition-colors border border-white/20">
              <svg width="24" height="24" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.1" d="M6 18L18 6M6 6l12 12"/>
              </svg>
            </button>
            
            <!-- Tên sản phẩm nổi bật trên ảnh -->
            <h3 class="absolute bottom-4 left-6 right-6 text-2xl font-black text-white drop-shadow-md">
              {{ product.name }}
            </h3>
          </div>

          <!-- Phần thân: Chi tiết, Giá và Nút Thanh toán -->
          <div class="p-6 bg-white">
            <p class="text-slate-600 leading-relaxed mb-6">{{ product.description }}</p>
            
            <!-- Hiển thị giá lớn, rõ ràng -->
            <div class="price-display flex items-center justify-between p-4 bg-slate-50 rounded-2xl border border-slate-100 mb-6">
              <span class="text-sm font-bold text-slate-400 uppercase tracking-widest">Thành tiền</span>
              <span class="text-3xl font-black text-rose-600">
                {{ formatPrice(product.price) }}
              </span>
            </div>

            <!-- Nút hành động chính (Thanh toán/Quay lại) -->
            <div class="flex gap-3">
              <button @click="$emit('close')" class="flex-1 h-14 bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold rounded-xl transition-all active:scale-95">
                Quay lại
              </button>
              
              <!-- Nút thanh toán nổi bật - Von Restorff Effect -->
              <button 
                @click="$emit('pay')" 
                :disabled="paying || !isOnline"
                class="flex-[2] h-14 bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-600 hover:to-teal-700 text-white font-black rounded-xl shadow-lg shadow-emerald-500/20 flex items-center justify-center gap-2 transition-all active:scale-95 disabled:opacity-50 disabled:grayscale disabled:scale-100"
              >
                <!-- Icon Loading khi đang xử lý -->
                <svg v-if="paying" class="animate-spin h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <template v-else>
                  <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z" />
                  </svg>
                  <span>{{ isOnline ? 'THANH TOÁN NGAY' : 'MÁY NGOẠI TUYẾN' }}</span>
                </template>
              </button>
            </div>

            <!-- Cam kết bảo mật/Tin cậy -->
            <div class="mt-6 pt-4 border-t border-slate-50 flex items-center justify-center gap-2">
              <svg class="w-4 h-4 text-emerald-500" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M2.166 4.9L10 .3l7.834 4.6a1 1 0 01.5.866v7.068a1 1 0 01-.5.866L10 18.3l-7.834-4.6a1 1 0 01-.5-.866V5.766a1 1 0 01.5-.866zm8.834 2.8a1 1 0 10-2 0v3.586L7.707 10.293a1 1 0 10-1.414 1.414l2 2a1 1 0 001.414 0l4-4a1 1 0 00-1.414-1.414L11 11.586V7.7z" clip-rule="evenodd" />
              </svg>
              <span class="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Thanh toán an toàn qua PayOS</span>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
/**
 * ProductModal Component
 * Giao diện chi tiết sản phẩm và nút bấm thanh toán chính.
 */
defineProps({
  product: { type: Object, default: null },
  isOnline: { type: Boolean, default: true },
  paying: { type: Boolean, default: false }
})

defineEmits(['close', 'pay'])

// Định dạng tiền tệ VND
const formatPrice = (p) => new Intl.NumberFormat('vi-VN', { style: 'currency', currency:'VND' }).format(p)
</script>

<style scoped>
.modal-overlay {
  position: fixed; inset: 0; z-index: 100;
  display: flex; align-items: flex-end; justify-content: center;
}
@media (min-width: 768px) { .modal-overlay { align-items: center; } }

.modal-backdrop {
  position: absolute; inset: 0;
  background: rgba(15, 23, 42, 0.4);
  backdrop-filter: blur(8px);
}

.product-modal {
  position: relative; z-index: 10;
  width: 100%; max-width: 30rem;
  background: white;
  border-radius: 2rem 2rem 0 0;
  overflow: hidden;
  max-height: 90vh;
}
@media (min-width: 768px) { .product-modal { border-radius: 2rem; } }

/* Hiệu ứng chuyển cảnh cho Modal */
.modal-enter-active, .modal-leave-active { transition: opacity 0.3s ease; }
.modal-enter-active .product-modal, .modal-leave-active .product-modal { transition: transform 0.4s cubic-bezier(0.16, 1, 0.3, 1); }
.modal-enter-from, .modal-leave-to { opacity: 0; }
.modal-enter-from .product-modal { transform: translateY(100%); }
@media (min-width: 768px) { .modal-enter-from .product-modal { transform: scale(0.9) translateY(40px); } }
</style>
