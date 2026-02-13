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
        async startPayment(productId, machineId = 1) {
            this.isProcessing = true
            this.paymentStatus = 'pending'
            try {
                const { createPayment } = await import('../api/payments.js')
                const result = await createPayment(productId, machineId)
                if (result.success) {
                    this.qrCodeUrl = result.qrCode
                    this.currentOrder = { orderCode: result.orderCode, checkoutUrl: result.checkoutUrl }
                } else {
                    this.paymentStatus = 'failed'
                    throw new Error(result.error)
                }
            } catch (error) {
                this.paymentStatus = 'failed'
                console.error(error)
                throw error
            } finally {
                this.isProcessing = false
            }
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
