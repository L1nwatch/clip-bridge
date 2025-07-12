import js from "@eslint/js";
import globals from "globals";
import pluginReact from "eslint-plugin-react";
import { defineConfig } from "eslint/config";


export default defineConfig([
  { files: ["**/*.{js,mjs,cjs,jsx}"], plugins: { js }, extends: ["js/recommended"] },
  // Node.js environment for main process files and build scripts
  { 
    files: ["src/main.js", "src/preload.js", "scripts/**/*.js"], 
    languageOptions: { 
      globals: {
        ...globals.node,
        ...globals.es2021
      },
      ecmaVersion: 2021,
      sourceType: "script"
    },
    rules: {
      "no-console": "off" // Allow console.log in Node.js scripts
    }
  },
  // Browser environment for renderer process files
  { 
    files: ["src/renderer/**/*.{js,jsx}", "public/**/*.js"], 
    languageOptions: { 
      globals: {
        ...globals.browser,
        ...globals.es2021
      }
    }
  },
  // Jest environment for test files
  {
    files: ["src/**/*.test.{js,jsx}", "src/**/__tests__/**/*.{js,jsx}", "src/setupTests.js"],
    languageOptions: {
      globals: {
        ...globals.browser,
        ...globals.jest,
        ...globals.node,
        ...globals.es2021
      }
    }
  },
  pluginReact.configs.flat.recommended,
  {
    settings: {
      react: {
        version: "detect"
      }
    }
  }
]);
