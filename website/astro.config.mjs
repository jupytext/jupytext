// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';

// https://astro.build/config
export default defineConfig({
	// Custom apex domain served from the root — see README for GitHub Pages setup.
	site: 'https://jupytext.org',
	base: '/',
	trailingSlash: 'ignore',
	integrations: [
		starlight({
			title: 'Jupytext',
			description:
				'Jupytext turns Jupyter notebooks into plain text files you can edit in any IDE, version control with clean diffs, and refactor with AI assistants.',
			logo: {
				src: './src/assets/logo.png',
				alt: 'Jupytext',
				replacesTitle: true,
			},
			favicon: '/favicon.svg',
			customCss: ['./src/styles/custom.css'],
			social: [
				{ icon: 'github', label: 'GitHub', href: 'https://github.com/jupytext/jupytext' },
			],
			editLink: {
				baseUrl: 'https://github.com/jupytext/jupytext/edit/main/website/',
			},
			sidebar: [
				{ label: 'Getting Started', items: [{ autogenerate: { directory: 'getting-started' } }] },
				{ label: 'Formats', items: [{ autogenerate: { directory: 'formats' } }] },
				{ label: 'Using Jupytext', items: [{ autogenerate: { directory: 'using' } }] },
				{ label: 'Integrations', items: [{ autogenerate: { directory: 'integrations' } }] },
				{ label: 'Reference', items: [{ autogenerate: { directory: 'reference' } }] },
			],
		}),
	],
});
