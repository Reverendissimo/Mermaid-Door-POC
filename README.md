# Mermaid Sesame NFC Door System

## Overview

This project provides a complete NFC-based access control solution, consisting of:
- **Mermaid Sesame Android App**: For managing, generating, and scanning NFC UIDs.
- **Python Door Controller**: For authenticating NFC cards and controlling a physical door lock using a PN532 NFC reader.

---

## Android App: Mermaid Sesame

### Features
- **Scan NFC Cards**: Reads the UID from any NFC card/tag and displays it in the format expected by the door controller (first 4 bytes reversed, hex string).
- **Modify UID**: Allows manual entry of a UID (hex only). The app always stores the normal UID, but displays the Python-style (reversed) UID.
- **Generate Random UID**: Instantly generates a random 12-character hex UID, stores it, and displays the Python-style UID.
- **Copy UID**: The displayed UID can be copied and used directly in the door controller system.
- **Debug Output**: Shows step-by-step debug information for NFC operations.
- **Modern UI**: Responsive, autoscaling layout with a custom background.

### UID Handling
- **Storage**: The app always stores the UID in its normal (non-reversed) form.
- **Display**: The app always displays the UID in the Python-compatible format (first 4 bytes reversed, as required by the door controller's hash logic).
- **Consistency**: Whether you scan, generate, or modify a UID, the app ensures the correct format is shown for use with the Python system.

### How to Use
1. **Scan**: Tap "Scan" and present a card. The UID will be shown in the correct format.
2. **Modify**: Tap "Modify" to enter a custom UID (hex only). Save to update.
3. **Generate Random ID**: Tap to create a new random UID.
4. **Copy UID**: Use the displayed UID for registration or testing with the door controller.

---

## Python Door Controller

- Located in the `python-door-code` directory.
- Uses a PN532 NFC reader to detect cards and read their UIDs.
- When a card is detected, the UID is reversed (first 4 bytes) and used in a hash with a PIN for authentication.
- The hash is checked against a list of valid hashes to grant or deny access.

### Integration Details
- **UID Format**: The Android app displays the UID in the exact format the Python code expects for hashing and authentication.
- **Workflow**:
    - Scan a card with the app, or generate/enter a UID.
    - Register the UID (as displayed in the app) in the door controller's hash list (with the correct PIN).
    - When the card is presented to the door controller, the UID will match and authentication will succeed.

---

## Repository Structure

- `android-pn532-hce/` — Android app source code (Mermaid Sesame)
- `python-door-code/` — Python door controller code
- `RGBmermaidCROP.png` — App background image
- `.gitignore` — Excludes build artifacts, APKs, and other non-source files

---

## Development Notes
- The Android app and Python controller are now fully compatible for UID handling.
- All UID logic is consistent: always store normal UID, always display Python-style UID.
- The repository is flat (no submodules), so all code is tracked in one place.

---

## License

MIT License. See individual folders for details. 