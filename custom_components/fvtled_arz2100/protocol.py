"""Protocol handler for FVTLED ARZ-2100 RGB controller."""
import asyncio
import logging
import socket
import time
from typing import Optional, Tuple

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
        """Establish TCP connection to the device."""
        try:
            if self._socket:
                self._socket.close()

            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.settimeout(10.0)  # Increased from 5.0 to 10.0 seconds
            self._socket.connect((self.host, self.port))
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
            except:
                pass
            self._socket = None

    def _send_command(self, command: bytes) -> Optional[bytes]:
        """Send a command and read response with retry logic."""
        last_error = None

        for attempt in range(self._max_retries):
            try:
                if not self._connect():
                    if attempt < self._max_retries - 1:
                        time.sleep(self._retry_delay)
                        continue
                    return None

                _LOGGER.debug("Sending command (attempt %d/%d): %s", attempt + 1, self._max_retries, command.hex())
                self._socket.send(command)

                # Read response
                response = self._socket.recv(STATUS_RESPONSE_LENGTH)
                _LOGGER.debug("Received response (%d bytes): %s", len(response), response.hex())

                return response
            except socket.timeout as err:
                last_error = err
                _LOGGER.warning("Command timeout (attempt %d/%d): %s", attempt + 1, self._max_retries, err)
                if attempt < self._max_retries - 1:
                    time.sleep(self._retry_delay)
                    continue
            except (socket.error, OSError) as err:
                last_error = err
                _LOGGER.warning("Error sending command (attempt %d/%d): %s", attempt + 1, self._max_retries, err)
                if attempt < self._max_retries - 1:
                    time.sleep(self._retry_delay)
                    continue
            finally:
                self._disconnect()

        _LOGGER.error("Error sending command after %d attempts: %s", self._max_retries, last_error)
        return None

    async def async_send_command(self, command: bytes) -> Optional[bytes]:
        """Send command asynchronously."""
        async with self._lock:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self._send_command, command)

    async def async_get_status(self) -> Optional[dict]:
        """Query device status."""
        command = bytes([CMD_QUERY_STATUS, 0x8A, 0x8B])
        response = await self.async_send_command(command)

        # Accept both 27 and 28-byte responses (device variants differ)
        if not response or len(response) < 27:
            _LOGGER.warning("Invalid status response length: %s", len(response) if response else 0)
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
        """Turn on the device."""
        command = bytes([CMD_POWER_ON, 0x23, 0x0F, 0xA3])
        response = await self.async_send_command(command)
        return response is not None

    async def async_turn_off(self) -> bool:
        """Turn off the device."""
        command = bytes([CMD_POWER_OFF, 0x24, 0x0F, 0xA4])
        response = await self.async_send_command(command)
        return response is not None

    async def async_set_color(
        self, red: int, green: int, blue: int, white: int = 0, brightness: int = 255
    ) -> bool:
        """
        Set color and brightness.

        Args:
            red: Red value (0-255)
            green: Green value (0-255)
            blue: Blue value (0-255)
            white: White value (0-255)
            brightness: Brightness (0-255)
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

        response = await self.async_send_command(command)
        return response is not None

    async def async_test_connection(self) -> bool:
        """Test if device is reachable."""
        status = await self.async_get_status()
        return status is not None
