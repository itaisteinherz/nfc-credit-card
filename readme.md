# nfc-credit-card

Demo program for parsing credit card data using an NFC reader.

_Only supports VISA cards at the moment._


## How to Use

- Install the requirements:
  ```sh
  $ pip install -r requirements.txt
  ```
  _(Note: prebuilt versions of `pyscard` are only available for Windows and macOS.)_
- Connect an NFC reader (I used [ACR1252](https://www.acs.com.hk/en/products/342/acr1252u-usb-nfc-reader-iii-nfc-forum-certified-reader/)).
- Place the card on the reader.
- Run the program:
  ```sh
  $ python main.py
  ```
- The script will connect to the card, select the appropriate application, and iteratively read its records until a
  record containing the PAN (card number) is found. It will then print the PAN as well as the expiration date.

The program processes the records locally, and does not send the credit card data to any remote server.


## License

MIT © [Itai Steinherz](https://github.com/itaisteinherz)
