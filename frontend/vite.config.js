import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'
import path from 'path'

export default defineConfig({
    resolve: {
        alias: {
            '@': path.resolve(__dirname, './src'),
        },
    },
    plugins: [
        vue(),
        tailwindcss(),
    ],
    server: {
        port: 3000,
        host: true,
        proxy: {
            '/api': {
                target: 'http://127.0.0.1:5001',
                changeOrigin: true,
            }
        }
    }
})
