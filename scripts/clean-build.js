#!/usr/bin/env node
// @ts-check

/**
 * @fileoverview Cross-platform script to clean build directories
 * @description This Node.js script removes build and dist/electron directories.
 * Works on Windows, macOS, and Linux.
 */

/** @type {import('fs')} */
const fs = require('fs');
/** @type {import('path')} */
const path = require('path');

/**
 * Removes a directory and all its contents
 * @param {string} dirPath - Path to the directory to remove
 * @returns {void}
 */
function removeDirectory(dirPath) {
  if (fs.existsSync(dirPath)) {
    try {
      fs.rmSync(dirPath, { recursive: true, force: true });
      console.log(`✅ Removed ${dirPath}`);
    } catch (error) {
      console.error(`❌ Failed to remove ${dirPath}:`, error.message);
      process.exit(1);
    }
  } else {
    console.log(`ℹ️  ${dirPath} does not exist, skipping`);
  }
}

console.log('🧹 Cleaning build directories...');

// Remove build directory
removeDirectory(path.join(__dirname, '../build'));

// Remove dist/electron directory
removeDirectory(path.join(__dirname, '../dist/electron'));

console.log('✅ Build directories cleaned successfully!');
