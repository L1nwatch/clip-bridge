#!/usr/bin/env node

/**
 * @fileoverview Dynamic port startup script for Electron + React app
 * @env node
 */

const { spawn } = require('child_process');
const getPort = require('get-port');
const path = require('path');
const fs = require('fs');

async function startWithDynamicPort() {
  try {
    // Find an available port starting from 3000
    // @ts-ignore - get-port module types
    const port = await getPort({ port: getPort.makeRange(3000, 3100) });
    
    console.log(`🚀 Starting React dev server on port ${port}`);
    
    // Update the main.js to use the dynamic port
    const mainJsPath = path.join(__dirname, '../src/main.js');
    let mainJsContent = fs.readFileSync(mainJsPath, 'utf8');
    
    // Replace the hardcoded localhost:3000 with the dynamic port
    mainJsContent = mainJsContent.replace(
      /http:\/\/localhost:3000/g,
      `http://localhost:${port}`
    );
    
    fs.writeFileSync(mainJsPath, mainJsContent);
    
    // Start React dev server with the found port
    const reactProcess = spawn('npm', ['run', 'react-start'], {
      env: { ...process.env, PORT: port.toString(), BROWSER: 'none' },
      stdio: 'inherit',
      shell: true
    });
    
    // Wait a bit for React to start, then start Electron
    setTimeout(() => {
      console.log(`🚀 Starting Electron, waiting for http://localhost:${port}`);
      
      const electronProcess = spawn('npx', ['wait-on', `http://localhost:${port}`, '&&', 'electron', '.'], {
        env: { ...process.env, NODE_ENV: 'development' },
        stdio: 'inherit',
        shell: true
      });
      
      electronProcess.on('error', (error) => {
        console.error('Failed to start Electron:', error);
      });
      
    }, 3000);
    
    reactProcess.on('error', (error) => {
      console.error('Failed to start React:', error);
    });
    
    // Handle cleanup
    process.on('SIGINT', () => {
      console.log('\n🛑 Shutting down...');
      reactProcess.kill();
      process.exit(0);
    });
    
  } catch (error) {
    console.error('Error starting with dynamic port:', error);
    process.exit(1);
  }
}

startWithDynamicPort();
