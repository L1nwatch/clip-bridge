#!/bin/bash

# sync-version.sh - Synchronize version numbers across all files
# Usage: ./scripts/sync-version.sh [version]
# If no version provided, uses the latest git tag

set -e

# Get the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Function to get the latest version from git tags
get_latest_version() {
    git tag --sort=-version:refname | head -n1 | sed 's/^v//'
}

# Function to update version in package.json
update_package_json() {
    local version=$1
    local file="$PROJECT_ROOT/package.json"
    
    if [[ -f "$file" ]]; then
        echo "Updating package.json version to $version"
        sed -i.bak "s/\"version\": \"[^\"]*\"/\"version\": \"$version\"/" "$file"
        rm -f "$file.bak"
    fi
}

# Function to update version in version_info.txt
update_version_info() {
    local version=$1
    local file="$PROJECT_ROOT/utils/version_info.txt"
    
    if [[ -f "$file" ]]; then
        echo "Updating version_info.txt version to $version"
        # Convert version like "0.1.12" to "(0,1,12,0)"
        IFS='.' read -ra PARTS <<< "$version"
        local major=${PARTS[0]:-0}
        local minor=${PARTS[1]:-0}
        local patch=${PARTS[2]:-0}
        local build=0
        
        # Update filevers and prodvers
        sed -i.bak "s/filevers=([0-9,]*)/filevers=($major,$minor,$patch,$build)/" "$file"
        sed -i.bak "s/prodvers=([0-9,]*)/prodvers=($major,$minor,$patch,$build)/" "$file"
        
        # Update FileVersion and ProductVersion strings
        sed -i.bak "s/StringStruct(u'FileVersion', u'[^']*')/StringStruct(u'FileVersion', u'$version.0')/" "$file"
        sed -i.bak "s/StringStruct(u'ProductVersion', u'[^']*')/StringStruct(u'ProductVersion', u'$version.0')/" "$file"
        
        rm -f "$file.bak"
    fi
}

# Function to update version in server.py
update_server_py() {
    local version=$1
    local file="$PROJECT_ROOT/utils/server.py"
    
    if [[ -f "$file" ]]; then
        echo "Updating server.py version to $version"
        sed -i.bak "s/\"version\": \"[^\"]*\"/\"version\": \"$version\"/g" "$file"
        rm -f "$file.bak"
    fi
}

# Function to update version in client.py
update_client_py() {
    local version=$1
    local file="$PROJECT_ROOT/utils/client.py"
    
    if [[ -f "$file" ]]; then
        echo "Updating client.py User-Agent version to $version"
        sed -i.bak "s/ClipboardBridge-Client\/[^\"]*\"/ClipboardBridge-Client\/$version\"/" "$file"
        rm -f "$file.bak"
    fi
}

# Function to update version in test files
update_test_files() {
    local version=$1
    local test_dir="$PROJECT_ROOT/utils/tests"
    
    if [[ -d "$test_dir" ]]; then
        echo "Updating test files version to $version"
        find "$test_dir" -name "*.py" -exec sed -i.bak "s/ClipboardBridge-Client\/[^\"]*\"/ClipboardBridge-Client\/$version\"/g" {} \;
        find "$test_dir" -name "*.bak" -delete
    fi
}

# Main function
main() {
    local version=$1
    
    # If no version provided, get from git tags
    if [[ -z "$version" ]]; then
        version=$(get_latest_version)
        if [[ -z "$version" ]]; then
            echo "Error: No version provided and no git tags found"
            exit 1
        fi
        echo "Using latest git tag version: $version"
    fi
    
    # Validate version format (basic check)
    if [[ ! "$version" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        echo "Error: Version must be in format X.Y.Z (e.g., 0.1.12)"
        exit 1
    fi
    
    echo "Synchronizing version to: $version"
    
    # Update all files
    update_package_json "$version"
    update_version_info "$version"
    update_server_py "$version"
    update_client_py "$version"
    update_test_files "$version"
    
    echo "Version synchronization complete!"
    echo ""
    echo "Files updated:"
    echo "  - package.json"
    echo "  - utils/version_info.txt"
    echo "  - utils/server.py"
    echo "  - utils/client.py"
    echo "  - utils/tests/*.py"
}

# Run main function with all arguments
main "$@"
