#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

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
