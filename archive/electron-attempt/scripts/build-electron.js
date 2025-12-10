const esbuild = require('esbuild');
const path = require('path');

const isWatch = process.argv.includes('--watch');

const mainConfig = {
  entryPoints: ['electron/main.js'],
  bundle: true,
  platform: 'node',
  target: 'node18',
  outfile: 'dist-electron/main.js',
  external: ['electron'],
  format: 'cjs',
  sourcemap: true,
};

const preloadConfig = {
  entryPoints: ['electron/preload.js'],
  bundle: true,
  platform: 'node',
  target: 'node18',
  outfile: 'dist-electron/preload.js',
  external: ['electron'],
  format: 'cjs',
  sourcemap: true,
};

async function build() {
  try {
    if (isWatch) {
      const mainCtx = await esbuild.context(mainConfig);
      const preloadCtx = await esbuild.context(preloadConfig);
      await Promise.all([mainCtx.watch(), preloadCtx.watch()]);
      console.log('Watching for changes...');
    } else {
      await Promise.all([
        esbuild.build(mainConfig),
        esbuild.build(preloadConfig),
      ]);
      console.log('Electron build complete.');
    }
  } catch (error) {
    console.error('Build failed:', error);
    process.exit(1);
  }
}

build();
