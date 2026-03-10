"""Protocol handler for FVTLED ARZ-2100 RGB controller."""
import asyncio
import logging
import socket
import time
from typing import Optional

from .const import (
    CMD_POWER_OFF,
    CMD_POWER_ON,
    CMD_QUERY_STATUS,
    CMD_SET_COLOR,
    DEFAULT_PORT,
    RESPONSE_HEADER,
    STATUS_RESPONSE_LENGTH,
)

_LOGGER = logging.getLogger(__name__)

# Timeout used when draining an initial greeting from the device (seconds)
_GREETING_DRAIN_TIMEOUT = 0.3
# Short timeout when checking for an optional ack on fire-and-forget commands
_ACK_DRAIN_TIMEOUT = 0.5


class FVTLEDARZ2100Protocol:
    """Protocol handler for FVTLED ARZ-2100 using 28-byte Zengge protocol."""

    def __init__(self, host: str, port: int = DEFAULT_PORT):
        """Initialize the protocol handler."""
        self.host = host
        self.port = port
        self._socket: Optional[socket.socket] = None
        self._lock = asyncio.Lock()
        self._max_retries = 3
        self._retry_delay = 0.5

    def _calculate_checksum(self, data: bytes) -> int:
        """Calculate checksum for command packet."""
        return sum(data) & 0xFF

    def _connect(self) -> bool:
        """Establish TCP connection to the device.

        Some firmware variants (e.g. WF.52/ZG-BL-3KEY) push a greeting packet
        (first byte 0xea) immediately after the TCP handshake completes.  We
        drain that unsolicited data so subsequent recv() calls see only the
        reply to the command we actually sent.
        """
        try:
            if self._socket:
                self._socket.close()

            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.settimeout(10.0)
            self._socket.connect((self.host, self.port))

            # Drain any greeting the device pushes on connect (e.g. 0xea …)
            self._socket.settimeout(_GREETING_DRAIN_TIMEOUT)
            try:
                greeting = self._socket.recv(64)
                _LOGGER.debug(
                    "Drained initial data on connect (%d bytes): %s",
                    len(greeting),
                    greeting.hex(),
                )
            except socket.timeout:
                pass  # No greeting – that's fine
            finally:
                self._socket.settimeout(10.0)

            _LOGGER.debug("Connected to %s:%s", self.host, self.port)
            return True
        except (socket.error, OSError) as err:
            _LOGGER.error("Failed to connect to %s:%s - %s", self.host, self.port, err)
            return False

    def _disconnect(self):
        """Close the TCP connection."""
        if self._socket:
            try:
                self._socket.close()
            except (OSError, socket.error):
                pass
            self._socket = None

    def _send_command(self, command: bytes, expect_response: bool = True) -> Optional[bytes]:
        """Send a command and optionally wait for a response.

        Args:
            command: Raw bytes to send.
            expect_response: When True (default) the method blocks until a
                response arrives (with retries on timeout).  When False the
                method sends the command and returns b"" on success (not None),
                after optionally draining a short ack window – this is the
                correct mode for power-on/off and set-color commands which the
                device does not acknowledge.

        Returns:
            - Response bytes for commands that return data.
            - b"" (empty bytes, truthy-check: ``is not None`` == True) when
              ``expect_response`` is False and the send succeeded.
            - None on connection or send failure.
        """
        last_error = None

        for attempt in range(self._max_retries):
            try:
                if not self._connect():
                    if attempt < self._max_retries - 1:
                        time.sleep(self._retry_delay)
                        continue
                    return None

                _LOGGER.debug(
                    "Sending command (attempt %d/%d): %s",
                    attempt + 1,
                    self._max_retries,
                    command.hex(),
                )
                self._socket.send(command)

                if not expect_response:
                    # Drain any optional ack without blocking
                    self._socket.settimeout(_ACK_DRAIN_TIMEOUT)
                    try:
                        ack = self._socket.recv(64)
                        _LOGGER.debug("Received optional ack: %s", ack.hex())
                    except socket.timeout:
                        pass  # No ack – expected for this device
                    # Return empty bytes to signal success (not None)
                    return b""

                # Wait for a full status response
                response = self._socket.recv(STATUS_RESPONSE_LENGTH)
                _LOGGER.debug(
                    "Received response (%d bytes): %s", len(response), response.hex()
                )
                return response

            except socket.timeout as err:
                last_error = err
                _LOGGER.warning(
                    "Command timeout (attempt %d/%d): %s",
                    attempt + 1,
                    self._max_retries,
                    err,
                )
                if attempt < self._max_retries - 1:
                    time.sleep(self._retry_delay)
            except (socket.error, OSError) as err:
                last_error = err
                _LOGGER.warning(
                    "Error sending command (attempt %d/%d): %s",
                    attempt + 1,
                    self._max_retries,
                    err,
                )
                if attempt < self._max_retries - 1:
                    time.sleep(self._retry_delay)
            finally:
                self._disconnect()

        _LOGGER.error(
            "Error sending command after %d attempts: %s", self._max_retries, last_error
        )
        return None

    async def async_send_command(
        self, command: bytes, expect_response: bool = True
    ) -> Optional[bytes]:
        """Send command asynchronously."""
        async with self._lock:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None,
                lambda: self._send_command(command, expect_response),
            )

    async def async_get_status(self) -> Optional[dict]:
        """Query device status."""
        command = bytes([CMD_QUERY_STATUS, 0x8A, 0x8B])
        response = await self.async_send_command(command)

        # Accept both 27 and 28-byte responses (device variants differ)
        if not response or len(response) < 27:
            _LOGGER.warning(
                "Invalid status response length: %s",
                len(response) if response else 0,
            )
            return None

        if response[0] != RESPONSE_HEADER:
            _LOGGER.warning("Invalid response header: 0x%02x", response[0])
            return None

        try:
            # Parse the response (27 or 28 bytes)
            # Byte 0: Response header (0x81)
            # Byte 1: Device type
            # Byte 2: Power state (0x23 = on, 0x24 = off)
            # Byte 3: Mode
            # Byte 4: Speed
            # Byte 5: Red value
            # Byte 6: Green value
            # Byte 7: Blue value
            # Byte 8: White value
            # Bytes 9-26: Extended data
            # Byte 27: Checksum (if present)
            return {
                "power": response[2] == 0x23,
                "mode": response[3],
                "speed": response[4],
                "red": response[5],
                "green": response[6],
                "blue": response[7],
                "white": response[8],
                "brightness": max(response[5], response[6], response[7], response[8]),
            }
        except (IndexError, ValueError) as err:
            _LOGGER.error("Error parsing status response: %s", err)
            return None

    async def async_turn_on(self) -> bool:
        """Turn on the device.

        The device does not send a response to power commands.
        We use expect_response=False to avoid blocking on a recv() that would
        never complete, which previously caused 30-second hangs.
        """
        command = bytes([CMD_POWER_ON, 0x23, 0x0F, 0xA3])
        response = await self.async_send_command(command, expect_response=False)
        return response is not None

    async def async_turn_off(self) -> bool:
        """Turn off the device.

        The device does not send a response to power commands.
        We use expect_response=False to avoid blocking on a recv() that would
        never complete, which previously caused 30-second hangs.
        """
        command = bytes([CMD_POWER_OFF, 0x24, 0x0F, 0xA4])
        response = await self.async_send_command(command, expect_response=False)
        return response is not None

    async def async_set_color(
        self, red: int, green: int, blue: int, white: int = 0, brightness: int = 255
    ) -> bool:
        """Set color and brightness.

        Args:
            red: Red value (0-255)
            green: Green value (0-255)
            blue: Blue value (0-255)
            white: White value (0-255)
            brightness: Brightness (0-255)

        The device does not send a response to color commands.
        We use expect_response=False to avoid blocking on a recv() that would
        never complete, which previously caused 30-second hangs.
        """
        # Scale colors by brightness
        scale = brightness / 255.0
        r = int(red * scale)
        g = int(green * scale)
        b = int(blue * scale)
        w = int(white * scale)

        # Build command
        command = bytes([CMD_SET_COLOR, r, g, b, w, 0x00, 0x0F])
        checksum = self._calculate_checksum(command)
        command += bytes([checksum])

        response = await self.async_send_command(command, expect_response=False)
        return response is not None

    async def async_test_connection(self) -> bool:
        """Test if device is reachable."""
        status = await self.async_get_status()
        return status is not None
