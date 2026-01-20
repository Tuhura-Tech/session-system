import node from '@astrojs/node';
import sitemap from '@astrojs/sitemap';
import tailwindcss from '@tailwindcss/vite';
import { defineConfig } from 'astro/config';

// https://astro.build/config
export default defineConfig({
	output: 'server',
	adapter: node({ mode: 'standalone' }),
	// site: 'https://sessions.tuhuratech.org.nz',
	integrations: [sitemap()],

	image: {
		service: {
			entrypoint: 'astro/assets/services/sharp',
		},
	},

	vite: {
		plugins: [tailwindcss()],
		optimizeDeps: { include: ['leaflet'] },
		cors: {
			origin: '*', // could be stricter
			methods: ['GET', 'HEAD', 'PUT', 'PATCH', 'POST', 'DELETE'],
			// preflightContinue: true, rely on cors middleware
			preflightContinue: true,
			optionsSuccessStatus: 204,
		},
	},
	security: {
		checkOrigin: false,
	},
});
