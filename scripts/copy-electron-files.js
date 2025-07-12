#!/usr/bin/env node

/**
 * @fileoverview Cross-platform script to copy Electron files for build
 * @description This Node.js script copies main.js and preload.js to the build directory
 * and updates package.json for Electron builds. Works on Windows, macOS, and Linux.
 */

/** @type {import('fs')} */
const fs = require('fs');
/** @type {import('path')} */
const path = require('path');

/**
 * Copies a file from source to destination
 * @param {string} src - Source file path
 * @param {string} dest - Destination file path
 * @returns {void}
 */
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

/**
 * Updates package.json in the build directory
 * @returns {void}
 */
function updatePackageJson() {
  try {
    /** @type {any} */
    // @ts-ignore - JSON module import
    const pkg = require('../package.json');
    
    // Create a minimal package.json for the built app
    const buildPkg = {
      name: pkg.name,
      version: pkg.version,
      description: pkg.description,
      author: pkg.author,
      homepage: pkg.homepage,
      main: 'electron.js',
      dependencies: pkg.dependencies
    };
    
    const buildPackagePath = path.join(__dirname, '../build/package.json');
    fs.writeFileSync(buildPackagePath, JSON.stringify(buildPkg, null, 2));
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
