#!/bin/bash
set -e

# Build web (PWA + Electron)
echo "Building web platform..."
cd web
pnpm build
pnpm electron:build

# Build iOS (TrollStore .ipa)
echo "Building iOS platform..."  
cd ../ios
xcodebuild -workspace Pinnacle.xcworkspace -scheme Pinnacle -archivePath Pinnacle.xcarchive archive
xcodebuild -exportArchive -archivePath Pinnacle.xcarchive -exportOptionsPlist ExportOptions.plist -exportPath .

# Build macOS (Self-signed .app)
echo "Building macOS platform..."
cd ../macos
xcodebuild -workspace Pinnacle.xcworkspace -scheme Pinnacle -configuration Release CODE_SIGN_IDENTITY="" CODE_SIGNING_REQUIRED=NO

echo "Build complete! Outputs:"
ls -la ../outputs
