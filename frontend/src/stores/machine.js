import { defineStore } from 'pinia'

export const useMachineStore = defineStore('machine', {
    state: () => ({
        machineId: 'MACHINE_01',
        name: 'Máy Bán Hàng Tự Động #1',
        location: 'Sảnh chính - Tòa nhà A',
        status: 'online',
        slots: [],
        iotConnected: false
    }),

    actions: {
        updateStatus(newStatus) {
            this.status = newStatus
        },
        setIotConnection(status) {
            this.iotConnected = status
        }
    }
})
