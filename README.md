# Mermaid Sesame NFC Door System

## Overview

This project provides a complete NFC-based access control solution with **dual authentication support**:
- **Mermaid Sesame Android App**: Host Card Emulation (HCE) app that emulates an NFC card
- **Python Door Controller**: Authenticates both physical NFC cards and Android HCE devices using a PN532 NFC reader

---

## Dual Authentication System

### Supported Devices
1. **Physical NFC Cards** (Mifare/NTAG/ISO14443-3A): Standard NFC cards and tags
2. **Android HCE Devices**: Phones running the Mermaid Sesame app that emulate NFC cards

### Authentication Logic
The door controller uses a **two-step detection process**:
1. **Detect any card** (phone or physical) using standard NFC polling
2. **Send SELECT AID APDU** to check if it's an Android HCE device
   - **If AID responds**: Use the UID returned by the Android app
   - **If no AID response**: Use the hardware UID from the physical card

This ensures reliable distinction between phones and cards, even when phones present random hardware UIDs.

---

## Android App: Mermaid Sesame

### Features
- **Host Card Emulation (HCE)**: Emulates an NFC card that responds to SELECT AID commands
- **UID Management**: Generate, modify, and store custom UIDs for door access
- **Scan Physical Cards**: Read UIDs from physical NFC cards for registration
- **Modern UI**: Responsive design with custom background and intuitive controls
- **Debug Output**: Real-time feedback for NFC operations

### UID Handling
- **Storage**: Always stores UIDs in normal (non-reversed) hex format
- **Display**: Shows UIDs in Python-compatible format (first 4 bytes reversed)
- **AID Response**: When the door controller sends SELECT AID `"A0000001020304"`, the app responds with the user's selected UID

### How to Use
1. **Generate Random UID**: Tap to create a new random 12-character hex UID
2. **Modify UID**: Enter a custom UID (hex only) for specific access control
3. **Scan Physical Card**: Read UIDs from existing NFC cards for registration
4. **Use for Authentication**: The displayed UID is what the door controller will use

---

## Python Door Controller

Located in `python-door-code/`, the controller provides:
- **Dual NFC Support**: Handles both physical cards and Android HCE devices
- **PIN Authentication**: Optional PIN entry for two-factor security
- **MQTT Integration**: Event logging and system integration
- **Configurable AID**: Easy AID customization for different app versions

### Authentication Flow
1. **Card Detection**: PN532 detects any NFC device (phone or card)
2. **AID Check**: Sends SELECT AID APDU to check for Android HCE
3. **UID Extraction**: 
   - Android HCE: Uses UID returned by app response
   - Physical Card: Uses hardware UID from card
4. **Authentication**: Validates UID + PIN hash against authorized list
5. **Access Control**: Grants/denies door access based on authentication

### Configuration
- **AID**: `"A0000001020304"` (matches Android app registration)
- **UID Format**: 12-character hex strings for Android, variable length for physical cards
- **PIN Security**: Optional PIN requirement for enhanced security

---

## Repository Structure

```
Mermaid-sesame/
├── android-pn532-hce/          # Android HCE app source
│   └── android-hce-app/        # Main app code
├── python-door-code/           # Python door controller
│   ├── main.py                 # Main door control logic
│   ├── pn532.py               # NFC communication
│   └── README.md              # Door controller documentation
├── RGBmermaidCROP.png         # App background image
├── README.md                  # This file
└── .gitignore                # Excludes build artifacts
```

---

## Integration Details

### AID Configuration
- **Standard AID**: `"A0000001020304"` (configured in both Android app and Python code)
- **Registration**: Android app registers for this AID in `apduservice.xml`
- **Communication**: Python code sends SELECT AID APDU with this value

### UID Format Consistency
- **Android App**: Stores normal UID, displays Python-style UID (first 4 bytes reversed)
- **Python Controller**: Expects Python-style UID for authentication
- **Physical Cards**: Hardware UID used directly (no reversal needed)

### Security Features
- **Dual Authentication**: Supports both card types seamlessly
- **PIN Protection**: Optional PIN requirement for enhanced security
- **UID Validation**: Hex-only UID input with length validation
- **Error Handling**: Graceful handling of communication failures

---

## Development Notes

- **Repository Structure**: Flat repository (no submodules) for easy management
- **Build System**: Android app uses Gradle with Android 12 SDK
- **NFC Standards**: Implements ISO14443-4 (HCE) and ISO14443-3A (physical cards)
- **Cross-Platform**: Python controller runs on Raspberry Pi or similar hardware

---

## License

MIT License. See individual folders for details. 