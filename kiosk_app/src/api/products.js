/**
 * API service cho sản phẩm và máy bán hàng
 * Sử dụng các API endpoints từ file .env
 */

// API Endpoints - cấu hình từ .env
const API_CONFIG = {
  PRODUCT_API: 'http://10.237.239.166:5000/api/products',
  MACHINE_API: 'http://10.237.239.166:5000/api/machines',
  PAYMENT_API: 'http://10.237.239.166:5000/api/payments',
  SLOT_API: 'http://10.237.239.166:5000/api/slots'
};

/**
 * Lấy danh sách tất cả sản phẩm
 */
export async function getProducts() {
  try {
    const response = await fetch(API_CONFIG.PRODUCT_API);

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();

    // Chuyển đổi dữ liệu từ API sang format cho UI
    if (data.success && data.data) {
      const products = data.data.map(product => ({
        id: product.id,
        name: product.name,
        price: product.price,
        image_url: product.image || '/images/default-product.png',
        is_available: product.active !== false,
        stock: product.stock || 10, // Giá trị mặc định nếu không có
        description: product.description || '',
        category: product.category || 'Sản phẩm'
      }));

      return {
        success: true,
        products: products,
        message: data.message
      };
    } else if (Array.isArray(data)) {
      // Trường hợp API trả về mảng trực tiếp
      const products = data.map(product => ({
        id: product.id,
        name: product.name,
        price: product.price,
        image_url: product.image || '/images/default-product.png',
        is_available: product.active !== false,
        stock: product.stock || 10,
        description: product.description || '',
        category: product.category || 'Sản phẩm'
      }));

      return {
        success: true,
        products: products,
        message: 'Lấy danh sách sản phẩm thành công'
      };
    } else {
      throw new Error('Invalid API response format');
    }
  } catch (error) {
    console.error('Error fetching products:', error);
    return {
      success: false,
      products: [],
      error: error.message
    };
  }
}

/**
 * Lấy thông tin sản phẩm theo ID
 */
export async function getProductById(productId) {
  try {
    const response = await fetch(`${API_CONFIG.PRODUCT_API}/${productId}`);

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    const productData = data.data || data;

    const product = {
      id: productData.id,
      name: productData.name,
      price: productData.price,
      image_url: productData.image || '/images/default-product.png',
      is_available: productData.active !== false,
      stock: productData.stock || 10,
      description: productData.description || '',
      category: productData.category || 'Sản phẩm'
    };

    return {
      success: true,
      product
    };
  } catch (error) {
    console.error('Error fetching product:', error);
    return {
      success: false,
      product: null,
      error: error.message
    };
  }
}

/**
 * Lấy danh sách máy bán hàng
 */
export async function getMachines() {
  try {
    const response = await fetch(API_CONFIG.MACHINE_API);

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();

    if (data.success && data.data) {
      return {
        success: true,
        machines: data.data,
        message: data.message
      };
    } else if (Array.isArray(data)) {
      return {
        success: true,
        machines: data,
        message: 'Lấy danh sách máy thành công'
      };
    } else {
      throw new Error('Invalid API response format');
    }
  } catch (error) {
    console.error('Error fetching machines:', error);
    return {
      success: false,
      machines: [],
      error: error.message
    };
  }
}

/**
 * Lấy thông tin máy theo ID
 */
export async function getMachineById(machineId) {
  try {
    const response = await fetch(`${API_CONFIG.MACHINE_API}/${machineId}`);

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return {
      success: true,
      machine: data.data || data
    };
  } catch (error) {
    console.error('Error fetching machine:', error);
    return {
      success: false,
      machine: null,
      error: error.message
    };
  }
}

/**
 * Lấy danh sách slot của máy
 */
export async function getSlots(machineId = null) {
  try {
    let url = API_CONFIG.SLOT_API;
    if (machineId) {
      url += `?machine_id=${machineId}`;
    }

    const response = await fetch(url);

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();

    if (data.success && data.data) {
      return {
        success: true,
        slots: data.data,
        message: data.message
      };
    } else if (Array.isArray(data)) {
      return {
        success: true,
        slots: data,
        message: 'Lấy danh sách slot thành công'
      };
    } else {
      throw new Error('Invalid API response format');
    }
  } catch (error) {
    console.error('Error fetching slots:', error);
    return {
      success: false,
      slots: [],
      error: error.message
    };
  }
}

/**
 * Lấy thông tin slot theo ID
 */
export async function getSlotById(slotId) {
  try {
    const response = await fetch(`${API_CONFIG.SLOT_API}/${slotId}`);

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return {
      success: true,
      slot: data.data || data
    };
  } catch (error) {
    console.error('Error fetching slot:', error);
    return {
      success: false,
      slot: null,
      error: error.message
    };
  }
}

/**
 * Lấy sản phẩm theo slot và máy
 */
export async function getProductsByMachine(machineId) {
  try {
    // Lấy danh sách slots của máy
    const slotsResult = await getSlots(machineId);

    if (!slotsResult.success) {
      throw new Error(slotsResult.error);
    }

    // Lấy thông tin sản phẩm cho từng slot
    const productsWithSlots = [];

    for (const slot of slotsResult.slots) {
      if (slot.product_id && slot.quantity > 0) {
        const productResult = await getProductById(slot.product_id);

        if (productResult.success && productResult.product) {
          productsWithSlots.push({
            ...productResult.product,
            slot_no: slot.slot_no,
            slot_id: slot.id,
            stock: slot.quantity
          });
        }
      }
    }

    return {
      success: true,
      products: productsWithSlots,
      message: 'Lấy sản phẩm theo máy thành công'
    };
  } catch (error) {
    console.error('Error fetching products by machine:', error);
    return {
      success: false,
      products: [],
      error: error.message
    };
  }
}

/**
 * Tạo thanh toán cho sản phẩm
 */
export async function createPayment(machineId, productId, amount, slotNo = null) {
  try {
    const response = await fetch(`${API_CONFIG.PAYMENT_API}/create`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        machine_id: machineId,
        product_id: productId,
        amount: amount,
        slot_no: slotNo,
        payment_method: 'qr_code'
      })
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return {
      success: true,
      orderCode: data.order_code,
      checkoutUrl: data.checkout_url,
      qrUrl: data.qr_url || data.qr_code_url,
      orderId: data.order_id
    };
  } catch (error) {
    console.error('Error creating payment:', error);
    return {
      success: false,
      error: error.message
    };
  }
}

/**
 * Kiểm tra trạng thái đơn hàng
 */
export async function getOrderStatus(orderCode) {
  try {
    const response = await fetch(`${API_CONFIG.PAYMENT_API}/status/${orderCode}`);

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return {
      success: true,
      status: data.status,
      orderCode: data.order_code,
      order: data.order || data
    };
  } catch (error) {
    console.error('Error checking order status:', error);
    return {
      success: false,
      error: error.message
    };
  }
}

/**
 * Hủy đơn hàng
 */
export async function cancelOrder(orderCode) {
  try {
    const response = await fetch(`${API_CONFIG.PAYMENT_API}/cancel/${orderCode}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      }
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return {
      success: true,
      message: data.message || 'Đã hủy đơn hàng'
    };
  } catch (error) {
    console.error('Error canceling order:', error);
    return {
      success: false,
      error: error.message
    };
  }
}

// Export API config để sử dụng ở nơi khác nếu cần
export { API_CONFIG };