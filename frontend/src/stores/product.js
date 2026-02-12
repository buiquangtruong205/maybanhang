import { defineStore } from 'pinia'

export const useProductStore = defineStore('product', {
    state: () => ({
        products: [],
        loading: false,
        error: null,
        selectedCategory: 'all'
    }),

    getters: {
        filteredProducts: (state) => {
            if (state.selectedCategory === 'all') return state.products
            return state.products.filter(p => p.category === state.selectedCategory)
        }
    },

    actions: {
        async fetchProducts() {
            this.loading = true
            try {
                // Giả lập gọi API - sau này sẽ thay bằng axios call
                // const response = await axios.get('/products')
                // this.products = response.data
                console.log('Fetching products...')
            } catch (err) {
                this.error = err.message
            } finally {
                this.loading = false
            }
        }
    }
})
