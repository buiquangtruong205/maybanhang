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
                const { getProducts } = await import('../api/products.js')
                const result = await getProducts()
                if (result.success) {
                    this.products = result.products
                } else {
                    this.error = result.error
                }
            } catch (err) {
                this.error = err.message
            } finally {
                this.loading = false
            }
        }
    }
})
