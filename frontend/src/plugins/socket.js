import { io } from "socket.io-client";
import { reactive } from "vue";

// Trạng thái kết nối (Reactive để dùng trong UI nếu cần)
export const socketState = reactive({
    connected: false,
});

// Khởi tạo connection
// Hardcode localhost:5001 cho môi trường dev để tránh vấn đề proxy/env
// Lưu ý: Backend đã mount socket tại '/socket.io'
const URL = "http://localhost:5001";

export const socket = io(URL, {
    path: "/socket.io", // Quan trọng: Phải khớp với đường dẫn mount ở Backend
    autoConnect: true,
    transports: ["websocket", "polling"], // Ưu tiên websocket
    reconnectionRequests: 5,
    reconnectionDelay: 1000,
    withCredentials: false // Tránh lỗi CORS credentials
});

socket.on("connect", () => {
    socketState.connected = true;
    console.log("🟢 Socket connected:", socket.id);
});

socket.on("disconnect", () => {
    socketState.connected = false;
    console.log("🔴 Socket disconnected");
});

socket.on("connect_error", (err) => {
    console.error("⚠️ Socket connection error:", err);
});

// Helper để components dễ dàng import
export default socket;
