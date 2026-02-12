export const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'
export const MQTT_BROKER = import.meta.env.VITE_MQTT_BROKER || 'ws://localhost:9001'

export const ORDER_STATUS = {
    PENDING: 'pending',
    PAID: 'paid',
    DISPENSING: 'dispensing',
    COMPLETED: 'completed',
    FAILED: 'failed',
    CANCELLED: 'cancelled'
}

export const MACHINE_STATUS = {
    ONLINE: 'online',
    OFFLINE: 'offline',
    ERROR: 'error',
    MAINTENANCE: 'maintenance'
}

export const PAYMENT_METHOD = {
    CASH: 'cash',
    VNQR: 'vnqr',
    MOMO: 'momo'
}
