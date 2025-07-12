#!/usr/bin/env node

/**
 * @fileoverview Cross-platform script to copy Electron files for build
 * @description This Node.js script copies main.js and preload.js to the build directory
 * and updates package.json for Electron builds. Works on Windows, macOS, and Linux.
 */

const fs = require('fs');
const path = require('path');

function copyFile(src, dest) {
  try {
    // Ensure destination directory exists
    const destDir = path.dirname(dest);
    if (!fs.existsSync(destDir)) {
      fs.mkdirSync(destDir, { recursive: true });
    }
    
    fs.copyFileSync(src, dest);
    console.log(`✅ Copied ${src} to ${dest}`);
  } catch (error) {
    console.error(`❌ Failed to copy ${src} to ${dest}:`, error.message);
    process.exit(1);
  }
}

function updatePackageJson() {
  try {
    const pkg = require('../package.json');
    pkg.main = 'electron.js';
    
    const buildPackagePath = path.join(__dirname, '../build/package.json');
    fs.writeFileSync(buildPackagePath, JSON.stringify(pkg, null, 2));
    console.log(`✅ Updated build/package.json`);
  } catch (error) {
    console.error(`❌ Failed to update package.json:`, error.message);
    process.exit(1);
  }
}

console.log('📦 Copying Electron files...');

// Copy main.js to build/electron.js
copyFile(
  path.join(__dirname, '../src/main.js'),
  path.join(__dirname, '../build/electron.js')
);

// Copy preload.js to build/
copyFile(
  path.join(__dirname, '../src/preload.js'),
  path.join(__dirname, '../build/preload.js')
);

// Update package.json in build directory
updatePackageJson();

console.log('✅ All Electron files copied successfully!');
