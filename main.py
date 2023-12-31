import logging
import re
import sys
from dataclasses import dataclass
from functools import cached_property
from typing import Tuple, Optional

from smartcard.CardType import AnyCardType
from smartcard.CardRequest import CardRequest
from smartcard.CardConnection import CardConnection
from smartcard.util import toHexString

VISA_PAN_PATTERN = r'4[0-9]{15}'


@dataclass
class Record:
    sfi: int
    record_number: int

    response: bytes
    sw1: int
    sw2: int

    @cached_property
    def text_response(self) -> str:
        return toHexString(self.response).replace(' ', '')

    @cached_property
    def visa_pan(self) -> Optional[str]:
        match = re.search(VISA_PAN_PATTERN, self.text_response)
        if match is None:
            return None

        return match.group()

    @cached_property
    def visa_expiration_date(self) -> Optional[Tuple[int, int]]:
        if self.visa_pan is None:
            return None

        expiration_date = self.text_response[30:34]
        return int(expiration_date[2:]), int(expiration_date[:2])


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    handlers=[logging.StreamHandler(sys.stdout)],
    format='%(asctime)s [%(levelname)s] %(filename)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


def create_card_connection() -> CardConnection:
    # Create a CardRequest object to request a card from the reader
    card_request = CardRequest(timeout=10, cardType=AnyCardType())

    # Wait for a card to be available
    card_service = card_request.waitforcard()

    # Connect to the card's connection
    card_connection = card_service.connection

    return card_connection


def select_visa_application(card_connection: CardConnection):
    # SELECT the VISA application (based on the AID)
    select_visa_command = [0x00, 0xA4, 0x04, 0x00, 0x07, 0xA0, 0x00, 0x00, 0x00, 0x03, 0x10, 0x10, 0x00]
    response, sw1, sw2 = card_connection.transmit(select_visa_command)
    if sw1 == 0x90 and sw2 == 0x00:
        logging.info("SELECT VISA Successful")
    else:
        logging.error("SELECT VISA Failed [%s %s]: %s", hex(sw1), hex(sw2), toHexString(response))
        raise RuntimeError


def read_record(card_connection: CardConnection, sfi: int, record_number: int) -> Record:
    read_record_command = [0x00, 0xB2, record_number, (sfi << 3) | 4, 0x00]
    response, sw1, sw2 = card_connection.transmit(read_record_command)
    text_response = toHexString(response)
    logging.debug("Received response [%s %s]: %s", sw1, sw2, text_response)
    if sw1 == 0x90 and sw2 == 0x00:
        logging.debug("READ RECORD (SFI: %s, Record: %s): %s", hex(sfi), hex(record_number), text_response)
        return Record(sfi, record_number, response, sw1, sw2)
    else:
        raise RuntimeError(f'Failed to read record (SFI: {hex(sfi)}, Record: {hex(record_number)})')


def find_pan_record(card_connection: CardConnection) -> Record:
    # Enumerate and fetch all files
    for sfi in range(1, 32):  # Iterate through possible SFIs (Short File Identifiers)
        # Enumerate and fetch all records in the file
        for record_number in range(1, 16):  # Iterate through possible record numbers
            try:
                record = read_record(card_connection, sfi, record_number)
                if record.visa_pan is not None:
                    return record
            except RuntimeError as e:
                logging.debug(str(e))
                continue

    raise RuntimeError('PAN record not found on card')


def main():
    logging.info('Connecting to card...')
    card_connection = create_card_connection()
    card_connection.connect()
    logging.info('Connected to card')

    select_visa_application(card_connection)

    pan_record = find_pan_record(card_connection)

    logging.info('PAN: %s', pan_record.visa_pan)
    logging.info('Expiration date: %d/%d', pan_record.visa_expiration_date[0], pan_record.visa_expiration_date[1])

    # Disconnect from the card
    card_connection.disconnect()

    logging.info('Disconnected from card')


if __name__ == '__main__':
    main()
