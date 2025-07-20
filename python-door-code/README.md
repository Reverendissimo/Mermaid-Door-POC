# Python Door Code (PN532 + Android HCE Support)

This project provides code for a door access system using a PN532 NFC reader, supporting both:
- **Normal NFC cards** (Mifare/NTAG/ISO14443-3A)
- **Android phones running a Host Card Emulation (HCE) app** (ISO-DEP/ISO14443-4)

## Files

- **main.py**: Main application logic, handles NFC reading, keypad input, door control, and network communication.
- **pn532.py**: Driver for the PN532 NFC reader (UART), with support for both passive UID reading and APDU (ISO-DEP) communication for Android HCE.

---

## How It Works

### 1. **Normal NFC Cards (Mifare/NTAG/ISO14443-3A)**
- The system uses the PN532 to detect a card and reads its UID at the hardware level.
- The UID is used for authentication (e.g., to unlock a door).

### 2. **Android HCE App (ISO-DEP/ISO14443-4)**
- When a phone running the compatible Android HCE app is detected, the reader:
  1. Sends a **SELECT AID APDU** (`00A4040007A0000001020304`) to the phone.
  2. The app responds with the UID set in the app.
  3. The system uses this UID for authentication, just like a normal card.
- If the APDU fails (not an HCE device), the system falls back to using the normal UID.

### 3. **Keypad and Door Control**
- The system can prompt for a PIN via a keypad.
- If the UID+PIN hash matches a known value, the door is unlocked.
- All events can be sent over MQTT for logging or integration.

---

## Code Structure

### main.py
- **Keypad**: Handles PIN entry and feedback LEDs.
- **Net**: Manages WiFi and MQTT communication.
- **Door**: Controls the door lock relay.
- **Nfc**: Handles NFC reading, including both normal cards and Android HCE.
- **handle_auth**: Main authentication loop (waits for card, gets PIN, checks hash, unlocks door).
- **main()**: Starts all async tasks (NFC, keypad, door, network).

### pn532.py
- **PN532Uart**: Low-level driver for the PN532 over UART.
  - `read_passive_target()`: Reads the UID of a normal card.
  - `send_apdu(target_number, apdu)`: Sends an APDU command (for Android HCE/ISO-DEP).
- **APDU SELECT AID**: Used to select the Android HCE app and get the app’s UID.

---

## How to Use

1. **Connect the PN532 to your microcontroller (UART).**
2. **Run the code on your device (MicroPython/ESP32/etc).**
3. **Scan a card or phone:**
   - If it’s a normal card, the UID is used.
   - If it’s an Android phone with the HCE app, the app’s UID is used (after APDU exchange).
4. **Enter PIN on the keypad (if required).**
5. **Door unlocks if UID+PIN hash matches.**

---

## Customization
- **AID/APDU**: If you change the AID in your Android app, update the SELECT AID APDU in `main.py` and `pn532.py`.
- **Authentication logic**: You can change how hashes are generated or how access is granted.
- **MQTT/Network**: Integrate with your own backend or logging system.

---

## References
- [PN532 UART MicroPython Driver (original repo)](https://github.com/insighio/micropython-pn532-uart)
- [Android HCE documentation](https://developer.android.com/guide/topics/connectivity/nfc/hce)
- [APDU SELECT command details](https://www.cardwerk.com/smartcard_standard_ISO7816-4_6_basic_organizations.aspx)

---

## License
MIT License (see source files for details) 