require('dotenv').config();
const bip39 = require('bip39');
const bitcoin = require('bitcoinjs-lib');
const { ECPair } = bitcoin;
const ethers = require('ethers');
const axios = require('axios');
const { Worker, isMainThread, parentPort } = require('worker_threads');
const TelegramBot = require('node-telegram-bot-api');

// Load sensitive data from .env file
const TELEGRAM_BOT_TOKEN = process.env.TELEGRAM_BOT_TOKEN;
const TELEGRAM_CHAT_ID = process.env.TELEGRAM_CHAT_ID;
const ETH_API_KEY = process.env.ETH_API_KEY;

const bot = new TelegramBot(TELEGRAM_BOT_TOKEN, { polling: false });

const BTC_API = 'https://blockchain.info/q/addressbalance/';
const ETH_API = 'https://api.etherscan.io/api?module=account&action=balance&address=';

const MAX_WORKERS = 4;
let totalGenerated = 0;

// Function to check Bitcoin balance
async function getBTCBalance(address) {
    try {
        const response = await axios.get(`${BTC_API}${address}?confirmations=0`);
        return parseFloat(response.data) / 1e8; // Convert Satoshis to BTC
    } catch (error) {
        return 0;
    }
}

// Function to check Ethereum balance
async function getETHBalance(address) {
    try {
        const response = await axios.get(`${ETH_API}${address}&apikey=${ETH_API_KEY}`);
        return parseFloat(response.data.result) / 1e18; // Convert Wei to ETH
    } catch (error) {
        return 0;
    }
}

// Function to generate wallets (BTC + ETH)
function generateWallet() {
    // Generate mnemonic (12 words)
    const mnemonic = bip39.generateMnemonic(128);
    const seed = bip39.mnemonicToSeedSync(mnemonic);
    
    // Bitcoin keypair (ECPair instead of bip32)
    const keyPair = ECPair.makeRandom();
    const { address: btcAddress } = bitcoin.payments.p2pkh({ pubkey: keyPair.publicKey });

    // Ethereum wallet
    const ethWallet = ethers.Wallet.fromMnemonic(mnemonic);
    const ethAddress = ethWallet.address;

    return { mnemonic, btcAddress, ethAddress };
}

// Function to check wallet balances
async function checkWallet() {
    const { mnemonic, btcAddress, ethAddress } = generateWallet();
    const btcBalance = await getBTCBalance(btcAddress);
    const ethBalance = await getETHBalance(ethAddress);

    totalGenerated++;

    if (btcBalance > 0.000000001 || ethBalance > 0.000000001) {
        const message = `🔹 Wallet Found!\n🔑 Mnemonic: ${mnemonic}\n\n💰 BTC: ${btcBalance}\n📍 BTC Address: ${btcAddress}\n\n💰 ETH: ${ethBalance}\n📍 ETH Address: ${ethAddress}`;
        bot.sendMessage(TELEGRAM_CHAT_ID, message);
    }
}

// Multi-threading to speed up generation
if (isMainThread) {
    for (let i = 0; i < MAX_WORKERS; i++) {
        const worker = new Worker(__filename);
        worker.on('message', msg => console.log(msg));
    }

    setInterval(() => {
        bot.sendMessage(TELEGRAM_CHAT_ID, `🔥 Total Generations: ${totalGenerated}`);
    }, 300000); // Every 5 minutes
} else {
    setInterval(checkWallet, 500);
}
