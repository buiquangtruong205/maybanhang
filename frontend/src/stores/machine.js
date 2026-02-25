import { defineStore } from 'pinia'
import { getMachines } from '../api/admin.js'

export const useMachineStore = defineStore('machine', {
    state: () => ({
        machineId: null,
        name: '',
        location: '',
        status: 'offline',
        slots: [],
        iotConnected: false,
        daLayDuLieu: false // đánh dấu đã gọi API chưa
    }),

    actions: {
        /**
         * Lấy thông tin máy từ API.
         * Mặc định lấy máy đầu tiên (cho hệ thống 1 máy).
         */
        async layThongTinMay() {
            try {
                const danhSachMay = await getMachines()
                if (Array.isArray(danhSachMay) && danhSachMay.length > 0) {
                    const may = danhSachMay[0]
                    this.machineId = may.id
                    this.name = may.name
                    this.location = may.location
                    this.status = may.status || 'offline'
                    this.daLayDuLieu = true
                }
            } catch (loi) {
                console.error('❌ Lỗi lấy thông tin máy:', loi)
                // Giữ giá trị mặc định nếu API lỗi
            }
        },

        capNhatTrangThai(trangThaiMoi) {
            this.status = trangThaiMoi
        },

        datKetNoiIoT(trangThai) {
            this.iotConnected = trangThai
        }
    }
})
