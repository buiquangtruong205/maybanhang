<template>
  <div class="qrcode-container">
    <canvas 
      ref="qrCanvas" 
      :width="size" 
      :height="size"
      class="qr-canvas"
    ></canvas>
  </div>
</template>

<script>
export default {
  name: 'Qrcode',
  props: {
    value: {
      type: String,
      required: true
    },
    size: {
      type: Number,
      default: 200
    },
    level: {
      type: String,
      default: 'M',
      validator: (value) => ['L', 'M', 'Q', 'H'].includes(value)
    }
  },
  mounted() {
    this.generateQR();
  },
  watch: {
    value() {
      this.generateQR();
    },
    size() {
      this.generateQR();
    }
  },
  methods: {
    generateQR() {
      if (!this.value) return;
      
      // Simple QR code generation using a library or service
      // For now, we'll use a QR code API service
      this.generateQRFromAPI();
    },

    async generateQRFromAPI() {
      try {
        const canvas = this.$refs.qrCanvas;
        const ctx = canvas.getContext('2d');
        
        // Clear canvas
        ctx.clearRect(0, 0, this.size, this.size);
        
        // Use QR Server API to generate QR code
        const qrUrl = `https://api.qrserver.com/v1/create-qr-code/?size=${this.size}x${this.size}&data=${encodeURIComponent(this.value)}&ecc=${this.level}`;
        
        const img = new Image();
        img.crossOrigin = 'anonymous';
        
        img.onload = () => {
          ctx.drawImage(img, 0, 0, this.size, this.size);
        };
        
        img.onerror = () => {
          // Fallback: draw a placeholder
          this.drawPlaceholder(ctx);
        };
        
        img.src = qrUrl;
        
      } catch (error) {
        console.error('QR generation error:', error);
        this.drawPlaceholder(this.$refs.qrCanvas.getContext('2d'));
      }
    },

    drawPlaceholder(ctx) {
      // Draw a simple placeholder when QR generation fails
      ctx.fillStyle = '#f0f0f0';
      ctx.fillRect(0, 0, this.size, this.size);
      
      ctx.fillStyle = '#666';
      ctx.font = '16px Arial';
      ctx.textAlign = 'center';
      ctx.fillText('QR Code', this.size / 2, this.size / 2 - 10);
      ctx.fillText('Loading...', this.size / 2, this.size / 2 + 10);
    }
  }
};
</script>

<style scoped>
.qrcode-container {
  display: inline-block;
}

.qr-canvas {
  border: 1px solid #ddd;
  border-radius: 8px;
  background: white;
}
</style>
