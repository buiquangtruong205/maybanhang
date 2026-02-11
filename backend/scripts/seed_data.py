#!/usr/bin/env python3
"""
ESP32 Simulator - Giả lập ESP32 để test hệ thống
"""
import requests
import time
import json
import threading
from datetime import datetime

class VendingMachineSimulator:
    def __init__(self, backend_url="http://localhost:5000"):
        self.backend_url = backend_url
        self.machine_id = "VM001"
        self.products = {}  # Sẽ load từ API
        self.is_running = False
        self.current_order = None
        
        # Load products từ API
        self.load_products_from_api()
        
    def load_products_from_api(self):
        """Load danh sách sản phẩm từ API"""
        try:
            print(f"🔄 Đang tải sản phẩm từ {self.backend_url}/api/products...")
            response = requests.get(f"{self.backend_url}/api/products", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and data.get("data"):
                    self.products = {}
                    for product in data["data"]:
                        self.products[product["id"]] = {
                            "name": product["name"],
                            "price": product["price"],
                            "stock": product["stock"],
                            "description": product.get("description", ""),
                            "category": product.get("category", "")
                        }
                    print(f"✅ Đã tải {len(self.products)} sản phẩm từ API")
                else:
                    print("❌ API trả về dữ liệu không hợp lệ")
                    self.use_fallback_products()
            else:
                print(f"❌ Lỗi API: {response.status_code}")
                self.use_fallback_products()
                
        except Exception as e:
            print(f"❌ Lỗi kết nối API: {e}")
            self.use_fallback_products()
    
    def use_fallback_products(self):
        """Sử dụng dữ liệu sản phẩm dự phòng"""
        print("🔄 Sử dụng dữ liệu sản phẩm dự phòng...")
        self.products = {
            1: {"name": "Coca Cola", "price": 15000, "stock": 10, "description": "Nước ngọt", "category": "Nước ngọt"},
            2: {"name": "Pepsi", "price": 15000, "stock": 8, "description": "Nước ngọt", "category": "Nước ngọt"},
            3: {"name": "Sprite", "price": 12000, "stock": 5, "description": "Nước ngọt", "category": "Nước ngọt"},
            4: {"name": "Fanta", "price": 12000, "stock": 7, "description": "Nước ngọt", "category": "Nước ngọt"}
        }
        
    def start_simulation(self):
        """Bắt đầu giả lập"""
        self.is_running = True
        print(f"🤖 ESP32 Simulator started - Machine ID: {self.machine_id}")
        print(f"📡 Backend URL: {self.backend_url}")
        
        # Thread để kiểm tra trạng thái thanh toán
        payment_thread = threading.Thread(target=self.check_payment_status)
        payment_thread.daemon = True
        payment_thread.start()
        
        # Thread để gửi heartbeat
        heartbeat_thread = threading.Thread(target=self.send_heartbeat)
        heartbeat_thread.daemon = True
        heartbeat_thread.start()
        
        self.main_loop()
    
    def main_loop(self):
        """Vòng lặp chính của máy bán hàng"""
        while self.is_running:
            try:
                print("\n" + "="*50)
                print("🏪 VENDING MACHINE SIMULATOR")
                print("="*50)
                print("1. Hiển thị sản phẩm")
                print("2. Reload sản phẩm từ API")
                print("3. Chọn sản phẩm và tạo thanh toán")
                print("4. Kiểm tra trạng thái thanh toán")
                print("5. Giả lập xuất hàng")
                print("6. Cập nhật stock (API)")
                print("7. Test API endpoints")
                print("8. Thoát")
                
                choice = input("\nChọn chức năng (1-8): ").strip()
                
                if choice == "1":
                    self.display_products()
                elif choice == "2":
                    self.load_products_from_api()
                elif choice == "3":
                    self.create_payment()
                elif choice == "4":
                    self.check_current_payment()
                elif choice == "5":
                    self.simulate_dispense()
                elif choice == "6":
                    self.update_stock_api()
                elif choice == "7":
                    self.test_api_endpoints()
                elif choice == "8":
                    self.is_running = False
                    print("👋 Simulator stopped")
                    break
                else:
                    print("❌ Lựa chọn không hợp lệ")
                    
            except KeyboardInterrupt:
                self.is_running = False
                print("\n👋 Simulator stopped")
                break
            except Exception as e:
                print(f"❌ Lỗi: {e}")
    
    def display_products(self):
        """Hiển thị danh sách sản phẩm"""
        print("\n📦 DANH SÁCH SẢN PHẨM:")
        print("-" * 60)
        for pid, product in self.products.items():
            status = "✅ Còn hàng" if product["stock"] > 0 else "❌ Hết hàng"
            print(f"{pid}. {product['name']} - {product['price']:,}đ")
            print(f"   📝 {product.get('description', 'N/A')} | 📂 {product.get('category', 'N/A')}")
            print(f"   📦 Stock: {product['stock']} - {status}")
            print("-" * 60)
    
    def create_payment(self):
        """Tạo thanh toán mới"""
        self.display_products()
        
        try:
            product_id = int(input("\nChọn sản phẩm (ID): "))
            if product_id not in self.products:
                print("❌ Sản phẩm không tồn tại")
                return
            
            product = self.products[product_id]
            if product["stock"] <= 0:
                print("❌ Sản phẩm đã hết hàng")
                return
            
            # Gửi request tạo thanh toán
            payload = {
                "machine_id": self.machine_id,
                "product_id": product_id,
                "amount": product["price"]
            }
            
            print(f"💳 Tạo thanh toán cho {product['name']} - {product['price']:,}đ...")
            
            response = requests.post(f"{self.backend_url}/api/create-payment", json=payload, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                self.current_order = {
                    "order_code": data["order_code"],
                    "product_id": product_id,
                    "amount": product["price"],
                    "checkout_url": data.get("checkout_url")
                }
                
                print(f"✅ Thanh toán được tạo thành công!")
                print(f"📱 Mã đơn hàng: {data['order_code']}")
                print(f"🔗 Link thanh toán: {data.get('checkout_url', 'N/A')}")
                
            else:
                print(f"❌ Lỗi tạo thanh toán: {response.text}")
                
        except ValueError:
            print("❌ Vui lòng nhập số hợp lệ")
        except Exception as e:
            print(f"❌ Lỗi: {e}")
    
    def check_current_payment(self):
        """Kiểm tra trạng thái thanh toán hiện tại"""
        if not self.current_order:
            print("❌ Không có đơn hàng nào đang chờ")
            return
        
        try:
            response = requests.get(f"{self.backend_url}/api/order-status/{self.current_order['order_code']}", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                status = data.get("status", "UNKNOWN")
                
                print(f"📊 Trạng thái đơn hàng {self.current_order['order_code']}: {status}")
                
                if status == "PAID":
                    print("✅ Thanh toán thành công! Sẵn sàng xuất hàng.")
                elif status == "PENDING":
                    print("⏳ Đang chờ thanh toán...")
                elif status == "CANCELLED":
                    print("❌ Thanh toán đã bị hủy")
                    self.current_order = None
                    
            else:
                print(f"❌ Lỗi kiểm tra trạng thái: {response.text}")
                
        except Exception as e:
            print(f"❌ Lỗi: {e}")
    
    def simulate_dispense(self):
        """Giả lập xuất hàng"""
        if not self.current_order:
            print("❌ Không có đơn hàng nào để xuất")
            return
        
        try:
            # Kiểm tra trạng thái thanh toán trước
            response = requests.get(f"{self.backend_url}/api/order-status/{self.current_order['order_code']}", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") != "PAID":
                    print("❌ Đơn hàng chưa được thanh toán")
                    return
            else:
                print("❌ Không thể kiểm tra trạng thái thanh toán")
                return
        
            # Giả lập quá trình xuất hàng
            product_id = self.current_order["product_id"]
            product = self.products[product_id]
            
            print(f"🔄 Đang xuất {product['name']}...")
            time.sleep(2)  # Giả lập thời gian xuất hàng
            
            # Giảm stock local
            self.products[product_id]["stock"] -= 1
            
            # Gửi thông báo xuất hàng thành công
            payload = {
                "order_code": self.current_order["order_code"],
                "machine_id": self.machine_id,
                "product_id": product_id,
                "status": "DISPENSED"
            }
            
            requests.post(f"{self.backend_url}/api/dispense-complete", json=payload, timeout=10)
            
            # Cập nhật stock qua API
            requests.post(f"{self.backend_url}/api/products/{product_id}/purchase", json={"quantity": 1}, timeout=10)
            
            print(f"✅ Xuất hàng thành công! {product['name']} đã được xuất.")
            print(f"📦 Stock còn lại: {self.products[product_id]['stock']}")
            
            self.current_order = None
            
        except Exception as e:
            print(f"❌ Lỗi xuất hàng: {e}")
    
    def update_stock_api(self):
        """Cập nhật stock sản phẩm qua API"""
        self.display_products()
        
        try:
            product_id = int(input("\nChọn sản phẩm để cập nhật stock (ID): "))
            if product_id not in self.products:
                print("❌ Sản phẩm không tồn tại")
                return
            
            new_stock = int(input(f"Nhập stock mới cho {self.products[product_id]['name']}: "))
            if new_stock < 0:
                print("❌ Stock không thể âm")
                return
            
            # Gửi request cập nhật stock
            response = requests.put(f"{self.backend_url}/api/products/{product_id}/stock", 
                                  params={"new_stock": new_stock}, timeout=10)
            
            if response.status_code == 200:
                self.products[product_id]["stock"] = new_stock
                print(f"✅ Đã cập nhật stock {self.products[product_id]['name']}: {new_stock}")
            else:
                print(f"❌ Lỗi cập nhật stock: {response.text}")
            
        except ValueError:
            print("❌ Vui lòng nhập số hợp lệ")
        except Exception as e:
            print(f"❌ Lỗi: {e}")
    
    def test_api_endpoints(self):
        """Test các API endpoints"""
        print("\n🧪 TESTING API ENDPOINTS")
        print("-" * 40)
        
        endpoints = [
            ("GET", "/api/products", "Lấy danh sách sản phẩm"),
            ("GET", "/api/products/1", "Lấy sản phẩm ID=1"),
            ("GET", "/", "Trang chủ"),
            ("GET", "/success", "Trang thành công"),
            ("GET", "/cancel", "Trang hủy")
        ]
        
        for method, endpoint, description in endpoints:
            try:
                url = f"{self.backend_url}{endpoint}"
                print(f"\n🔍 {method} {endpoint} - {description}")
                
                if method == "GET":
                    response = requests.get(url, timeout=5)
                
                if response.status_code == 200:
                    print(f"✅ Status: {response.status_code}")
                    if endpoint.startswith("/api/"):
                        try:
                            data = response.json()
                            print(f"📄 Response: {json.dumps(data, indent=2, ensure_ascii=False)[:200]}...")
                        except:
                            print(f"📄 Response: {response.text[:100]}...")
                    else:
                        print(f"📄 HTML Response: {len(response.text)} characters")
                else:
                    print(f"❌ Status: {response.status_code}")
                    print(f"📄 Error: {response.text[:100]}...")
                    
            except Exception as e:
                print(f"❌ Lỗi: {e}")
    
    def check_payment_status(self):
        """Thread kiểm tra trạng thái thanh toán định kỳ"""
        while self.is_running:
            if self.current_order:
                try:
                    response = requests.get(f"{self.backend_url}/api/order-status/{self.current_order['order_code']}", timeout=5)
                    
                    if response.status_code == 200:
                        data = response.json()
                        if data.get("status") == "PAID":
                            print(f"\n🔔 THÔNG BÁO: Đơn hàng {self.current_order['order_code']} đã được thanh toán!")
                            
                except Exception:
                    pass  # Bỏ qua lỗi trong background check
            
            time.sleep(5)  # Kiểm tra mỗi 5 giây
    
    def send_heartbeat(self):
        """Gửi heartbeat để báo máy đang hoạt động"""
        while self.is_running:
            try:
                payload = {
                    "machine_id": self.machine_id,
                    "timestamp": datetime.now().isoformat(),
                    "status": "ONLINE",
                    "products": self.products
                }
                
                requests.post(f"{self.backend_url}/api/heartbeat", json=payload, timeout=5)
                
            except Exception:
                pass  # Bỏ qua lỗi heartbeat
            
            time.sleep(30)  # Gửi heartbeat mỗi 30 giây

if __name__ == "__main__":
    print("🚀 Khởi động Vending Machine Simulator...")
    simulator = VendingMachineSimulator()
    simulator.start_simulation()