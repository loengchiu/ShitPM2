import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// base: './' 使构建产物使用相对资源路径，可部署到 Cloudflare Pages 任意子路径
export default defineConfig({
  base: './',
  plugins: [react()],
  build: {
    outDir: 'dist',
    emptyOutDir: true,
  },
});
