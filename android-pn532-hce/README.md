# Mermaid Sesame - Android HCE App

A Host Card Emulation (HCE) Android app that emulates an NFC card for door access control systems. The app responds to SELECT AID commands from NFC readers and provides a user-configurable UID for authentication.

## Features

- **Host Card Emulation (HCE)**: Emulates an NFC card that responds to SELECT AID APDU commands
- **UID Management**: Generate, modify, and store custom UIDs for door access
- **Scan Physical Cards**: Read UIDs from existing NFC cards for registration
- **Modern UI**: Responsive design with custom background and intuitive controls
- **Debug Output**: Real-time feedback for NFC operations
- **NFC Permission Handling**: Proper permission checks and user guidance

## How It Works

### HCE Concept
The app uses Android's Host Card Emulation (HCE) feature to emulate an NFC card:
- **Registration**: App registers for AID `"A0000001020304"` in the system
- **Background Service**: HCE service runs in background (no app launch required)
- **APDU Response**: When reader sends SELECT AID command, app responds with user's UID
- **Security**: Screen must be on (Android security policy), but device can be locked

### UID Handling
- **Storage**: Always stores UIDs in normal (non-reversed) hex format
- **Display**: Shows UIDs in Python-compatible format (first 4 bytes reversed)
- **AID Response**: When door controller sends SELECT AID `"A0000001020304"`, app responds with user's selected UID

## Installation

### Option 1: Build from Source
```bash
# Clone the repository
git clone https://github.com/Reverendissimo/Mermaid-Door-POC.git
cd Mermaid-Door-POC/android-pn532-hce/android-hce-app

# Build the APK
./gradlew assembleDebug
```

### Option 2: Download APK
The debug APK is available via HTTP server:
```bash
# Start HTTP server (from project root)
cd android-pn532-hce/android-hce-app/app/build/outputs/apk/debug
python3 -m http.server 8000
```

Then download from: `http://your-server-ip:8000/app-debug.apk`

## Usage

### Initial Setup
1. **Install the app** on your Android device
2. **Grant NFC permissions** when prompted
3. **Enable NFC** in device settings if not already enabled

### Managing UIDs
1. **Generate Random UID**: Tap the "Generate Random ID" button to create a new 12-character hex UID
2. **Modify UID**: Tap "Modify" to enter a custom UID (hex only, 0-9, A-F)
3. **Scan Physical Card**: Tap "Scan" to read UIDs from existing NFC cards
4. **Save Changes**: The app automatically saves UID changes to persistent storage

### Using for Door Access
1. **Note the Displayed UID**: The app shows the UID in Python-compatible format
2. **Register with Door Controller**: Add this UID to your door controller's authorized list
3. **Present Phone**: Hold your phone to the door controller's NFC reader
4. **Authentication**: The door controller will receive your app's UID and authenticate

## Technical Details

### AID Configuration
- **Standard AID**: `"A0000001020304"` (configured in `apduservice.xml`)
- **Service Registration**: App registers for this AID in `AndroidManifest.xml`
- **APDU Response**: When reader sends SELECT AID, app responds with user's UID

### UID Format
- **Storage Format**: Normal hex string (e.g., `"1234567890AB"`)
- **Display Format**: Python-style (first 4 bytes reversed, e.g., `"7856341290AB"`)
- **Length**: 12-character hex strings for generated/modified UIDs

### Security Features
- **NFC Permissions**: Proper permission handling with user guidance
- **UID Validation**: Hex-only input with length validation
- **Background Operation**: HCE service runs without app being open
- **Screen Requirement**: Device screen must be on for NFC communication

## Integration with Door Controller

This app is designed to work with the Python door controller in the `python-door-code` directory:

1. **AID Matching**: Both app and controller use the same AID `"A0000001020304"`
2. **UID Format**: App provides UIDs in the format expected by the controller
3. **Authentication Flow**: Controller sends SELECT AID, app responds with UID, controller authenticates

## Development

### Project Structure
```
android-hce-app/
├── app/src/main/
│   ├── java/com/lexycon/hostcardemulation/
│   │   ├── MainActivity.kt              # Main UI and NFC scanning
│   │   ├── HostCardEmulatorService.kt   # HCE service for APDU handling
│   │   └── DataStoreUtil.kt            # UID storage and management
│   ├── res/
│   │   ├── layout/activity_main.xml     # UI layout
│   │   └── xml/apduservice.xml         # AID registration
│   └── AndroidManifest.xml             # App permissions and service registration
└── build.gradle                        # Build configuration
```

### Key Components
- **MainActivity**: UI for UID management and NFC scanning
- **HostCardEmulatorService**: HCE service that responds to SELECT AID commands
- **DataStoreUtil**: Manages UID storage in SharedPreferences
- **apduservice.xml**: Registers the app for the standard AID

### Building
```bash
# Ensure Android SDK is configured
./gradlew clean
./gradlew assembleDebug
```

## Troubleshooting

### Common Issues
1. **NFC Not Working**: Ensure NFC is enabled and permissions are granted
2. **App Not Responding**: Make sure the device screen is on
3. **UID Not Updating**: Check that the hex input is valid (0-9, A-F only)
4. **Build Errors**: Ensure Android SDK and Gradle are properly configured

### Debug Information
- The app provides debug output for NFC operations
- Check the debug text area for step-by-step information
- Logs are available in Android Studio or via `adb logcat`

## License

MIT License. See the main project README for details.
