import http from './http.js'

/**
 * Product API — GET /api/v1/products
 */
export async function getProducts() {
  try {
    const data = await http.get('/products/')
    // V2 backend returns array directly from SQLAlchemy
    const products = Array.isArray(data) ? data : (data.data || [])
    return {
      success: true,
      products: products.map(p => ({
        id: p.id,
        name: p.name,
        price: p.price,
        image_url: p.image_url || p.image || '/images/default-product.png',
        is_available: p.is_available !== false,
        stock: p.stock ?? 10,
        description: p.description || '',
        category: p.category || 'Đồ uống'
      }))
    }
  } catch (error) {
    return { success: false, products: [], error: error.message }
  }
}

export async function getProductById(productId) {
  try {
    const data = await http.get(`/products/${productId}`)
    return { success: true, product: data }
  } catch (error) {
    return { success: false, product: null, error: error.message }
  }
}