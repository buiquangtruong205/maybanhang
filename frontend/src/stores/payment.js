import { defineStore } from 'pinia'

export const usePaymentStore = defineStore('payment', {
    state: () => ({
        isProcessing: false,
        currentOrder: null,
        paymentStatus: 'none', // none, pending, success, failed
        qrCodeUrl: null,
        amount: 0
    }),

    actions: {
        startPayment(order, amount) {
            this.currentOrder = order
            this.amount = amount
            this.isProcessing = true
            this.paymentStatus = 'pending'
        },
        setQrCode(url) {
            this.qrCodeUrl = url
        },
        completePayment(success = true) {
            this.paymentStatus = success ? 'success' : 'failed'
            this.isProcessing = false
        },
        resetPayment() {
            this.currentOrder = null
            this.amount = 0
            this.paymentStatus = 'none'
            this.isProcessing = false
            this.qrCodeUrl = null
        }
    }
})
