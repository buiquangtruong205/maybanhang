import { io } from "socket.io-client";
import { reactive } from "vue";

// Trạng thái kết nối (Reactive để dùng trong UI nếu cần)
export const socketState = reactive({
    connected: false,
});

// Lấy URL socket từ biến môi trường hoặc tự detect từ hostname hiện tại
// Ưu tiên: VITE_SOCKET_URL > cùng hostname với trang web (port 5001) > localhost
const laySocketURL = () => {
    // 1. Ưu tiên biến môi trường
    if (import.meta.env.VITE_SOCKET_URL) {
        return import.meta.env.VITE_SOCKET_URL;
    }

    // 2. Trong chế độ phát triển, dùng localhost
    if (import.meta.env.DEV) {
        return "http://localhost:5001";
    }

    // 3. Production: dùng cùng hostname với trang web
    return `${window.location.protocol}//${window.location.hostname}:5001`;
};

const URL = laySocketURL();

export const socket = io(URL, {
    path: "/socket.io", // Quan trọng: Phải khớp với đường dẫn mount ở Backend
    autoConnect: true,
    transports: ["websocket", "polling"], // Ưu tiên websocket
    reconnectionAttempts: 5,
    reconnectionDelay: 1000,
    withCredentials: false // Tránh lỗi CORS credentials
});

socket.on("connect", () => {
    socketState.connected = true;
    console.log("🟢 Socket đã kết nối:", socket.id);
});

socket.on("disconnect", () => {
    socketState.connected = false;
    console.log("🔴 Socket đã ngắt kết nối");
});

socket.on("connect_error", (loi) => {
    console.error("⚠️ Lỗi kết nối Socket:", loi.message);
});

// Hàm tiện ích để components dễ dàng import
export default socket;
