import tailwindcss from '@tailwindcss/vite';
import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';

export default defineConfig({
	plugins: [react(), tailwindcss()],
	server: {
		port: 3001,
	},
	build: {
		// Ensure assets are referenced with relative paths
		assetsDir: 'assets',
	},
});
