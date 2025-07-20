from pn532 import PN532Uart, PN532Error
import utime
import machine
import hashlib
import os
import asyncio
import network
import requests
import _thread
from umqtt.simple import MQTTClient

DEBUG = True

class Keypad:
    CMD_RESET = 'F'
    CMD_ENABLE_FEEDBACK = 'Q'
    CMD_LED_GREEN = 'G'
    CMD_LED_RED = 'R'
    CMD_GRANTED = 'H' # AKA happy
    CMD_DENIED = 'S' # AKA sad

    def __init__(self, uart):
        self._uart = uart

    def write(self, data):
        self._uart.write(data)
        self._uart.flush()

    async def get_pin(self, timeout_ms=10000):
        uart = self._uart

        # discard previous bytes
        uart.read(uart.any())

        uart.write(self.CMD_ENABLE_FEEDBACK)
        uart.write(self.CMD_LED_GREEN)
        uart.flush()

        data = bytearray()
        while len(data) < 4 and timeout_ms > 0:
            n = uart.any()
            for c in uart.read(n):
                if ord('0') <= c <= ord('9'):
                    # print(f"rx: {c}")
                    data.append(c)
            await asyncio.sleep(0.1)
            timeout_ms -= 100

        return data[:4]


class Net:
    def __init__(self):
        self._connected = False
        self._wlan = network.WLAN(network.STA_IF)

        self._events = []
        # keepalive is needed due to: https://github.com/eclipse/mosquitto/issues/2462
        self._mqtt = MQTTClient("lock", "10.11.1.1", keepalive=5)
        self._mqtt.set_callback(self._mqtt_cb)

    async def loop(self):
        self.start()
        while True:
            self.update()
            await asyncio.sleep(0.5)

    def _mqtt_cb(self, topic, msg):
        if topic == b'locks/internal/command':
            if msg == b'sync':
                try:
                    print("starting sync")
                    # TODO: add auth support to http server
                    url = "http://10.11.1.1:8000/hashes/internal"
                    print(f"fetching: {url}")
                    rsp = requests.get(url)
                    print(f"sync code: {rsp.status_code}")
                    with open('hashes_new', 'wb') as f:
                        if 200 <= rsp.status_code < 300:
                            while True:
                                chunk = rsp.raw.read(512)
                                if not chunk:
                                    break
                                f.write(chunk)
                    os.rename('hashes_new', 'hashes')
                    print("sync finished")
                    self.send_event("sync", 'success'.encode())
                except Exception as e:
                    print(f"sync error: {e}")
                    self.send_event("sync", 'fail'.encode())
            else:
                print(f"uncrecognised command: {msg}")


    def send_event(self, name, payload):
        # TODO: limit number of events in queue
        self._events.append((name, payload))


    def _run_mqtt(self):
        mqtt = self._mqtt
        while True:
            try:
                while True:
                    mqtt.connect()
                    mqtt.publish("locks/internal/mac", self._wlan.config('mac').hex())
                    mqtt.subscribe("locks/internal/command")

                    i = 0
                    while True:
                        try:
                            while True:
                                name, payload = self._events.pop()
                                print("sending event")
                                mqtt.sock.setblocking(True)
                                mqtt.publish(f"locks/internal/events/{name}", payload)
                        except IndexError:
                            pass

                        if i == 10:
                            i = 0
                            mqtt.ping()
                        else:
                            i += 1

                        mqtt.check_msg()
                        utime.sleep(0.25)

            except Exception as e:
                print(f"mqtt exception: {e}")
                utime.sleep(6)

    def start(self):
        self._wlan.active(True)
        # for net in self._wlan.scan():
        #     print(f'scan: {net}')
        print("mac:", self._wlan.config('mac').hex())

        _thread.start_new_thread(self._run_mqtt, ())

        with open('wifi', 'r') as f:
            ssid = f.readline().strip()
            key = f.readline().strip()

        if not self._wlan.isconnected():
            print(f'connecting to network ssid={ssid!r}')
            self._wlan.connect(ssid, key)


    def update(self):
        if self._wlan.isconnected():
            if not self._connected:
                print('network config:', self._wlan.ifconfig())
                self._connected = True
        else:
            if self._connected:
                print('disconnected')
                self._connected = False


class Door:
    def __init__(self, pin):
        self._pin = pin

    def unlock(self):
        if self._pin is not None:
            self._pin.value(1)

    def lock(self):
        if self._pin is not None:
            self._pin.value(0)

def generate_hash(card_uid, pin):
    card_uid = bytes(reversed(card_uid[:4])).hex()
    s = "{:08x}:{}".format(int(pin), card_uid)
    hash=hashlib.sha256(s.encode('ascii')).digest().hex()
    return hash


async def handle_auth(nfc, keypad, door, net):
    while True:
        card_info = await nfc.wait_uid()
        if isinstance(card_info, tuple):
            card_type, card_uid = card_info
        else:
            card_type, card_uid = "mifare", card_info

        if card_type == "mifare":
            uid_hex = ''.join('{:02x}'.format(x) for x in card_uid)
            print("Card UUID (Mifare): " + uid_hex)
            used_uid = card_uid
        elif card_type == "android":
            print("Card UUID (Android app): " + str(card_uid))
            # Convert to bytes for hashing if needed
            try:
                used_uid = bytes.fromhex(card_uid)
            except Exception:
                used_uid = card_uid.encode() if isinstance(card_uid, str) else card_uid
        else:
            print("Unknown card type")
            continue

        pin = await keypad.get_pin()
        keypad.write(keypad.CMD_RESET)

        if len(pin) < 4:
            print("Pin timeout")
            keypad.write(keypad.CMD_DENIED)
            await asyncio.sleep(0.5)
            keypad.write(keypad.CMD_RESET)
            continue

        hash = generate_hash(used_uid, pin)
        print(f'Card hash: {hash}')

        hash_found = False
        with open("hashes") as f:
            for user in f:
                if(user.strip() == hash):
                    hash_found = True
                    break

        net.send_event("hash", hash.encode())

        try:
            if hash_found:
                print('Known hash, opening door')
                keypad.write(keypad.CMD_GRANTED)
                door.unlock()
            else:
                print('Unknown hash, ignoring')
                keypad.write(keypad.CMD_DENIED)

            await asyncio.sleep(2)

        finally:
            door.lock()
            keypad.write(keypad.CMD_RESET)


class Nfc:
    def __init__(self):
        self._uids = []
        self._flag = asyncio.Event()

    async def wait_uid(self):
        # discard queued uids
        for _ in range(len(self._uids)):
            self._uids.pop()

        while not self._uids:
            await self._flag.wait()
            self._flag.clear()

        uid = None
        while self._uids:
            uid = self._uids.pop()
        return uid

    async def loop(self):
        rf = PN532Uart(2, rx=19, tx=22)

        try:
            rf.SAM_configuration()
            ic, ver, rev, support = rf.get_firmware_version()
            print(f'Found PN532 with firmware version: {ver}.{rev}')
        except Exception as e:
            print('No NFC reader (PN532) detected')
            raise

        # Standard AID for the Android app (must match the app's AID)
        ANDROID_AID = "A0000001020304"  # This is the default in the Android app

        while True:
            try:
                # 1. Wait for any card (phone or physical)
                uid = rf.read_passive_target()
                if uid is not None:
                    # 2. Always try SELECT AID APDU after card detection
                    #    If the app responds (returns a UID), use that UID for authentication.
                    #    If not, use the hardware UID from the card.
                    hce_uid = rf.read_hce_uid(aid_hex=ANDROID_AID)
                    if hce_uid:
                        # Android app responded: use the UID returned by the app
                        self._uids.append(("android", hce_uid))
                    else:
                        # No app response: use the hardware UID from the card
                        self._uids.append(("mifare", uid))
                    self._flag.set()
            except PN532Error as e:
                print('PN532:', e)

            rf.power_down()
            await asyncio.sleep(0.25)


async def main():
    print("Lock app wil start in 2s")
    await asyncio.sleep(2)

    keypad = Keypad(machine.UART(1, tx=16, rx=17, baudrate=9600))
    keypad.write(keypad.CMD_RESET)

    nfc = Nfc()

    door = Door(machine.Pin(2, machine.Pin.OUT))
    door.lock()

    net = Net()

    await asyncio.gather(
        handle_auth(nfc, keypad, door, net),
        nfc.loop(),
        net.loop()
    )


if __name__ == '__main__':
    asyncio.run(main())
