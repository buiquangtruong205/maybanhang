import http from './http.js'

/**
 * Payment API — POST /api/v1/payments/create
 */
export async function createPayment(productId, machineId = 1) {
    try {
        const data = await http.post('/payments/create', {
            product_id: productId,
            machine_id: machineId
        })
        return {
            success: true,
            orderCode: data.order_code,
            checkoutUrl: data.checkout_url,
            qrCode: data.qr_code
        }
    } catch (error) {
        return { success: false, error: error.message }
    }
}

/**
 * Get order status (polling)
 */
export async function getOrderStatus(orderCode) {
    try {
        const data = await http.get(`/orders/${orderCode}`)
        return {
            success: true,
            status: data.status,
            order: data
        }
    } catch (error) {
        return { success: false, error: error.message }
    }
}
