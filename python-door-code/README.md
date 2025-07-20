# Python Door Controller (PN532 + Android HCE Support)

This project implements a secure door access system using a PN532 NFC reader, supporting both:
- **Standard NFC cards** (Mifare/NTAG/ISO14443-3A)
- **Android phones running a custom Host Card Emulation (HCE) app** (ISO-DEP/ISO14443-4)

---

## Features

- **Dual Authentication:** Accepts both physical NFC cards and Android HCE emulated cards.
- **Keypad PIN Entry:** Optional PIN entry for two-factor authentication.
- **MQTT Integration:** Sends events for logging or integration with other systems.
- **Configurable AID:** Easily update the AID to match your Android app.

---

## File Overview

- **main.py**: Main application logic (NFC reading, keypad, door control, network).
- **pn532.py**: PN532 NFC reader driver (UART), with support for both passive UID and APDU (HCE) communication.

---

## How It Works

### 1. Card/Phone Detection Logic (IMPORTANT)
- The PN532 waits for any card (physical or phone) and reads its hardware UID.
- **After detecting any card, the system ALWAYS sends a SELECT AID APDU to the card.**
- If the card responds to the SELECT AID APDU, it is an **Android phone running the HCE app** (use the UID from the app's response).
- If the card does NOT respond to the SELECT AID APDU, it is a **physical card** (use the hardware UID).
- **This is the only reliable way to distinguish a phone from a card, since Android HCE always presents a random hardware UID.**

### 2. Authentication Flow
- The system waits for a card or phone.
- Prompts for a PIN via the keypad.
- Combines the UID (from app or card) and PIN, hashes them, and checks against a list of authorized hashes.
- If valid, the door is unlocked and an event is sent via MQTT.

---

## Usage

1. **Connect the PN532 to your microcontroller (UART).**
2. **Run the code on your device (MicroPython/ESP32/etc).**
3. **Scan a card or phone:**
   - If it’s a standard card, the UID is used (after AID check fails).
   - If it’s an Android phone with the HCE app, the app’s UID is used (after AID check succeeds).
4. **Enter PIN on the keypad (if required).**
5. **Door unlocks if UID+PIN hash matches an entry in the `hashes` file.**

---

## Customization

- **AID/APDU:**  
  If you change the AID in your Android app, update the `ANDROID_AID` variable in `main.py` and the call to `read_hce_uid` in `pn532.py`.
- **Authentication Logic:**  
  You can modify how hashes are generated or how access is granted in `generate_hash`.
- **MQTT/Network:**  
  Integrate with your own backend or logging system by modifying the `Net` class.

---

## Security Notes

- Always keep your `hashes` file secure.
- Use strong, unique PINs for each user.
- Change the AID in your Android app and Python code for additional security.

---

## References

- [PN532 UART MicroPython Driver (original repo)](https://github.com/insighio/micropython-pn532-uart)
- [Android HCE documentation](https://developer.android.com/guide/topics/connectivity/nfc/hce)
- [APDU SELECT command details](https://www.cardwerk.com/smartcard_standard_ISO7816-4_6_basic_organizations.aspx)

---

## License

MIT License (see source files for details) 