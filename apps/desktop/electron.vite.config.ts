import { defineConfig } from 'electron-vite'
import react from '@vitejs/plugin-react-swc'
import { resolve } from 'path'

export default defineConfig({
  main: {
    build: {
      rollupOptions: {
        input: resolve('src/main.ts'),
        external: ['electron']
      }
    }
  },
  preload: {
    build: {
      rollupOptions: {
        input: resolve('src/preload.ts'),
        external: ['electron']
      }
    }
  },
  renderer: {
    root: '.',
    plugins: [react()],
    resolve: {
      alias: {
        '@': resolve('src')
      }
    },
    build: {
      rollupOptions: {
        input: resolve('index.html')
      }
    }
  }
})
