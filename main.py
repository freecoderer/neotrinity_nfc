from pn532 import *
from web3 import Web3, HTTPProvider
from web3.middleware import geth_poa_middleware
from eth_account import Account
from dotenv import load_dotenv
import os
import RPi.GPIO as GPIO


def execute_ethereum_transaction():
    load_dotenv()

    # Ethereum 노드의 RPC 엔드포인트 입력
    web3 = Web3(Web3.HTTPProvider(os.environ.get('myendpoint')))

    # Initialize the address calling the functions/signing transactions
    caller = os.environ.get('mycaller')
    private_key = os.environ.get('myprivatekey')  # To sign the transaction

    # Verify if the connection is successful
    if web3.is_connected():
        print("-" * 50)
        print("Connection Successful")
        print("-" * 50)
    else:
        print("Connection Failed")
        return

    # Initialize address nonce
    nonce = web3.eth.get_transaction_count(caller)

    # 스마트 컨트랙트 ABI 및 주소 설정
    contract_abi = """

    [{"inputs":[{"internalType":"string","name":"_code","type":"string"}],"stateMutability":"nonpayable","type":"constructor"},{"anonymous":false,"inputs":[{"indexed":false,"internalType":"address","name":"reserver","type":"address"},{"indexed":true,"internalType":"uint256","name":"time","type":"uint256"}],"name":"roomOpened","type":"event"},{"anonymous":false,"inputs":[{"indexed":false,"internalType":"address","name":"reserver","type":"address"},{"indexed":true,"internalType":"uint256","name":"time","type":"uint256"}],"name":"roomReserved","type":"event"},{"inputs":[],"name":"code","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"timestamp","type":"uint256"}],"name":"minutesAndSeconds","outputs":[{"internalType":"uint256","name":"truncatedTimestamp","type":"uint256"}],"stateMutability":"pure","type":"function"},{"inputs":[{"internalType":"address","name":"reserverID","type":"address"}],"name":"openRoom","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"owner","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint16","name":"year","type":"uint16"},{"internalType":"uint8","name":"month","type":"uint8"},{"internalType":"uint8","name":"day","type":"uint8"},{"internalType":"uint8","name":"hour","type":"uint8"},{"internalType":"uint8","name":"period","type":"uint8"},{"internalType":"address","name":"reserver","type":"address"}],"name":"reserveRoom","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"}]

    """

    contract_address = os.environ.get('myaddress')

    # Create smart contract instance
    contract = web3.eth.contract(address=contract_address, abi=contract_abi)

    # initialize the chain id, we need it to build the transaction for replay protection
    Chain_id = web3.eth.chain_id

    # Call your function
    reserver_id = os.environ.get('myreverserid')# Replace with actual reserver ID
    call_function = contract.functions.openRoom(reserver_id).build_transaction({"chainId": Chain_id, "from": caller, "nonce": nonce})

    # Sign transaction
    signed_tx = web3.eth.account.sign_transaction(call_function, private_key=private_key)

    # Send transaction
    send_tx = web3.eth.send_raw_transaction(signed_tx.rawTransaction)

    # Wait for transaction receipt
    tx_receipt = web3.eth.wait_for_transaction_receipt(send_tx)

    print(tx_receipt['status'])
    # Check transaction status
    if tx_receipt['status']:
        print("Transaction successful.")
    else:
        print("Transaction failed.")


if __name__ == '__main__':
    try:
        pn532 = PN532_I2C(debug=False, reset=20, req=16)

        ic, ver, rev, support = pn532.get_firmware_version()
        print('Found PN532 with firmware version: {0}.{1}'.format(ver, rev))

        # Configure PN532 to communicate with MiFare cards
        pn532.SAM_configuration()

        print('Waiting for RFID/NFC card...')
        while True:
            # Check if a card is available to read
            uid = pn532.read_passive_target(timeout=0.5)
            print('.', end="")
            # Try again if no card is available.
            if uid is None:
                continue
            print('Found card with UID:', [hex(i) for i in uid])

            # 특정 UID 값과 일치하는 경우 Ethereum 트랜잭션 실행
            if [hex(i) for i in uid] == ['0x1', '0x23', '0x45', '0x67']:
                execute_ethereum_transaction()

    except Exception as e:
        print(e)
    finally:
        GPIO.cleanup()
