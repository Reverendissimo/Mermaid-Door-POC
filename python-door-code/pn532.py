# repo: https://github.com/insighio/micropython-pn532-uart
#
# MIT License
#
# Copyright (c) 2021 Infinite Tree Inc
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from micropython import const
import machine
import utime

# from pn532uart import PN532_UART
# import PN532

# PN532 Commands
_WAKEUP                        = b'\x55\x55\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
_COMMAND_GETFIRMWAREVERSION    = const(0x02)
_COMMAND_INLISTPASSIVETARGET   = const(0x4A)
_COMMAND_INRELEASE             = const(0x52)
_COMMAND_SAMCONFIGURATION      = const(0x14)
_COMMAND_RFCONFIGURATION       = const(0x32)
_COMMAND_POWERDOWN             = const(0x16)

# Send Frames
_PREAMBLE                      = const(0x00)
_STARTCODE1                    = const(0x00)
_STARTCODE2                    = const(0xFF)
_POSTAMBLE                     = const(0x00)

# Message parts
_HOSTTOPN532                   = const(0xD4)
_PN532TOHOST                   = const(0xD5)
_ACK                           = b'\x00\x00\xFF\x00\xFF\x00'
_FRAME_START                   = b'\x00\x00\xFF'

# Codes
_MIFARE_ISO14443A              = const(0x00)

class PN532Error(RuntimeError):
    pass

class PN532Uart(object):
    """
    Class for interacting with the PN532 via the uart interface.
    """
    def __init__(self, uart_no, tx=None, rx=None, debug=False):
        if tx and rx:
            self.uart = machine.UART(uart_no, baudrate=115200, tx=tx, rx=rx)
        else:
            self.uart = machine.UART(uart_no, baudrate=115200)

        self.debug = debug
        # self.swriter = asyncio.StreamWriter(self.uart, {})
        # self.sreader = asyncio.StreamReader(self.uart)

    def wait_read_len(self, len):
        timeout_ms = 1000
        start_time = utime.ticks_ms()
        end_time = start_time + timeout_ms
        while self.uart.any() < len and utime.ticks_ms() < end_time:
            continue

        if(utime.ticks_ms() >= end_time):
            raise PN532Error('No response from PN532!')

        return self.uart.read(len)

    def _write_frame(self, data):
        """Write a frame to the PN532 with the specified data bytearray."""
        assert data is not None and 1 < len(data) < 255, 'Data must be array of 1 to 255 bytes.'

        # Build frame to send as:
        # - Preamble (0x00)
        # - Start code  (0x00, 0xFF)
        # - Command length (1 byte)
        # - Command length checksum
        # - Command bytes
        # - Checksum
        # - Postamble (0x00)
        length = len(data)
        frame = bytearray(length+8)
        frame[0] = _PREAMBLE
        frame[1] = _STARTCODE1
        frame[2] = _STARTCODE2
        checksum = sum(frame[0:3])
        frame[3] = length & 0xFF
        frame[4] = (~length + 1) & 0xFF
        frame[5:-2] = data
        checksum += sum(data)
        frame[-2] = ~checksum & 0xFF
        frame[-1] = _POSTAMBLE

        # Send frame.
        if self.debug:
            print('_write_frame: ', [hex(i) for i in frame])

        # HACK! Timeouts can cause there to be data in the read buffer that was for an old command (ie read_passive_target).
        # Additonally, the device needs to be woken sometimes, and it seems safe to do that before every command.
        # TODO: Does WAKEUP cancel the passive read_command?
        # Before sending the real command, clear the read buffer
        self.uart.write(_WAKEUP)

        waiting = self.uart.any()
        while waiting > 0:
            if self.debug:
                print("Removing %d bytes in the read buffer")
            self.uart.read(waiting)
            waiting = self.uart.any()

        self.uart.write(bytes(frame))
        #self.uart.flush()

        ack = self.wait_read_len(len(_ACK))

        if self.debug:
            print('_write_frame: ACK: ', [hex(i) for i in ack])
        if ack != _ACK:
            raise PN532Error('Did not receive expected ACK from PN532!')

    def _read_frame(self):
        """
        Read a response frame from the PN532 and return the data inside the frame,
        otherwise raises an exception if there is an error parsing the frame.
        """
        # Read the Frame start and header
        response = self.wait_read_len(len(_FRAME_START)+2)
        if self.debug:
            print('_read_frame: frame_start + header:', [hex(i) for i in response])

        if len(response) < (len(_FRAME_START) + 2) or response[:-2] != _FRAME_START:
            raise PN532Error('Response does not begin with _FRAME_START!')

        # Read the header (length & length checksum) and make sure they match.
        frame_len = response[-2]
        frame_checksum = response[-1]
        if (frame_len + frame_checksum) & 0xFF != 0:
            raise PN532Error('Response length checksum did not match length!')

        # read the frame (data + data checksum + end frame) & validate
        data = self.wait_read_len(frame_len+2)

        if self.debug:
            print('_read_frame: data: ', [hex(i) for i in data])

        checksum = sum(data) & 0xFF
        if checksum != 0:
            raise PN532Error('Response checksum did not match expected value: ', checksum)

        if data[-1] != 0x00:
            raise PN532Error('Response does not include Frame End')

        # Return frame data.
        return data[0:frame_len]

    def call_function(self, command, params=[]):
        """
        Send specified command to the PN532 and return the response.
        Note: There is no timeout option. Use async.wait_for(function(), timeout) instead
        """
        data = bytearray(2 + len(params))
        data[0] = _HOSTTOPN532
        data[1] = command & 0xFF
        for i, val in enumerate(params):
            data[2+i] = val

        # Send the frame and read the response
        self._write_frame(data)
        response = self._read_frame()

        if len(response) < 2:
            raise PN532Error('Received smaller than expected frame')

        if not(response[0] == _PN532TOHOST and response[1] == (command+1)):
            raise PN532Error('Received unexpected command response!')

        # Return response data.
        return response[2:]

    def SAM_configuration(self):
        if self.debug:
            print("Sending SAM_CONFIGURATION")

        response = self.call_function(_COMMAND_SAMCONFIGURATION, params=[0x01])
        if self.debug:
            print('SAM_configuration:', response.hex())

        # Enable RF:
        #   0x32 - Cmd: RFConfiguration
        #   0x01 - Item: RF Field
        #   0x03 - AutoRFCA=on, RF=on
        self.call_function(_COMMAND_RFCONFIGURATION, params=[0x01, 0x03])

        # Return imidiately aftery trying once:
        #   0x32 - Cmd: RFConfiguration
        #   0x05 - Item: MaxRetries
        #   0x00 - 0 retries (1 try)
        #   0x00 - 0 retries (1 try)
        #   0x00 - 0 retries (1 try)
        self.call_function(_COMMAND_RFCONFIGURATION, params=[0x05, 0x00, 0x00, 0x00])

    def get_firmware_version(self):
        """
        Call PN532 GetFirmwareVersion function and return a tuple with the IC,
        Ver, Rev, and Support values.
        """
        if self.debug:
            print("Sending GET_FIRMWARE_VERSION")

        response = self.call_function(_COMMAND_GETFIRMWAREVERSION)
        if response is None:
            raise PN532Error('Failed to detect the PN532')
        return tuple(response)

    def read_passive_target(self, card_baud=_MIFARE_ISO14443A):
        """
        Wait for a MiFare card to be available and return its UID when found.
        Will wait up to timeout seconds and return None if no card is found,
        otherwise a bytearray with the UID of the found card is returned.
        """

        # Enable RF:
        #   0x32 - Cmd: RFConfiguration
        #   0x01 - Item: RF Field
        #   0x03 - AutoRFCA=on, RF=on
        self.call_function(_COMMAND_RFCONFIGURATION, params=[0x01, 0x03])

        if self.debug:
            print("Sending INIT_PASSIVE_TARGET")
        # Send passive read command for 1 card.  Expect at most a 7 byte UUID.
        response = self.call_function(_COMMAND_INLISTPASSIVETARGET, params=[0x01, card_baud])

        # Check only 1 card with up to a 7 byte UID is present.
        if response[0] == 0x00:
            return None
        if response[0] > 0x01:
            raise PN532Error('More than one card detected!')
        if response[5] > 7:
            raise PN532Error('Found card with unexpectedly long UID!')

        # Return UID of card.
        return response[6:6+response[5]]

    def power_down(self):
        # Disable RF:
        #   0x32 - Cmd: RFConfiguration
        #   0x01 - Item: RF Field
        #   0x00 - AutoRFCA=off, RF=off
        self.call_function(_COMMAND_RFCONFIGURATION, params=[0x01, 0x00])

        # Power down
        #   0x16 - Cmd: PowerDown
        #   0x10 - WakeUpEnable: 5 bit - HSU (UART)
        self.call_function(_COMMAND_POWERDOWN, params=[0x10])

    def release_targets(self):
        if self.debug:
            print("Release Targets")
        response = self.call_function(_COMMAND_INRELEASE, params=[0x00])

    def read_hce_uid(self, aid_hex):
        """
        Try to communicate with a Type 4A (Android HCE) tag by sending a SELECT AID APDU.
        Returns the UID string from the app, or None if not present.
        """
        # Enable RF
        self.call_function(_COMMAND_RFCONFIGURATION, params=[0x01, 0x03])
        if self.debug:
            print("Sending INIT_PASSIVE_TARGET for HCE")
        try:
            response = self.call_function(_COMMAND_INLISTPASSIVETARGET, params=[0x01, _MIFARE_ISO14443A])
        except PN532Error:
            return None
        if response[0] == 0x00:
            return None
        # Type 4A tag (Android HCE) will have SENS_RES = 0x44 0x00 and SEL_RES = 0x20
        # See NFC Forum Digital Protocol spec for details
        # We assume any card here could be HCE, so try APDU
        # Send SELECT AID APDU: 00 A4 04 00 <len> <AID>
        aid_bytes = bytearray.fromhex(aid_hex)
        apdu = bytearray([0x00, 0xA4, 0x04, 0x00, len(aid_bytes)]) + aid_bytes
        # InDataExchange command: 0x40, 0x01 (target 1), then APDU
        params = [0x40, 0x01] + list(apdu)
        try:
            apdu_response = self.call_function(0x40, params)
        except PN532Error:
            return None
        # The response should be the UID string (hex) from the app, possibly with status word 0x9000 at the end
        if not apdu_response:
            return None
        # Remove trailing status word if present (0x90 0x00)
        if len(apdu_response) >= 2 and apdu_response[-2:] == b'\x90\x00':
            apdu_response = apdu_response[:-2]
        # Return as string
        try:
            return apdu_response.decode('ascii')
        except Exception:
            return apdu_response.hex()
