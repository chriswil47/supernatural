require('dotenv').config(); // Load environment variables from .env
const bip39 = require('bip39');
const bip32 = require('bip32'); // Explicitly use bip32 for HD wallets
const { networks, payments } = require('bitcoinjs-lib');
const ethers = require('ethers');
const axios = require('axios');
const { Worker, isMainThread, parentPort } = require('worker_threads');
const TelegramBot = require('node-telegram-bot-api');

// Environment Variables (store sensitive data in .env)
const TELEGRAM_BOT_TOKEN = process.env.TELEGRAM_BOT_TOKEN;
const TELEGRAM_CHAT_ID = process.env.TELEGRAM_CHAT_ID;
const ETH_API_KEY = process.env.ETH_API_KEY;

// Validate Environment Variables
if (!TELEGRAM_BOT_TOKEN || !TELEGRAM_CHAT_ID || !ETH_API_KEY) {
    console.error("Missing environment variables. Check your .env file.");
    process.exit(1);
}

const bot = new TelegramBot(TELEGRAM_BOT_TOKEN, { polling: false });

const BTC_API = 'https://blockchain.info/q/addressbalance/';
const ETH_API = `https://api.etherscan.io/api?module=account&action=balance&apikey=${ETH_API_KEY}`;

const MAX_WORKERS = 4;
let totalGenerated = 0;

// Fetch BTC Balance
async function getBTCBalance(address) {
    try {
        const response = await axios.get(`${BTC_API}${address}?confirmations=0`);
        return parseFloat(response.data) / 1e8; // Convert Satoshis to BTC
    } catch (error) {
        console.error(`BTC API Error: ${error.message}`);
        return 0;
    }
}

// Fetch ETH Balance
async function getETHBalance(address) {
    try {
        const response = await axios.get(`${ETH_API}&address=${address}`);
        return parseFloat(response.data.result) / 1e18; // Convert Wei to ETH
    } catch (error) {
        console.error(`ETH API Error: ${error.message}`);
        return 0;
    }
}

// Generate Wallets (12-word mnemonic)
function generateWallet() {
    const mnemonic = bip39.generateMnemonic(128); // 12 words
    const seed = bip39.mnemonicToSeedSync(mnemonic);
    
    // Bitcoin Wallet (BIP32)
    const btcRoot = bip32.fromSeed(seed, networks.bitcoin);
    const btcNode = btcRoot.derivePath("m/44'/0'/0'/0/0");
    const { address: btcAddress } = payments.p2pkh({ pubkey: btcNode.publicKey, network: networks.bitcoin });

    // Ethereum Wallet
    const ethWallet = ethers.Wallet.fromMnemonic(mnemonic);
    const ethAddress = ethWallet.address;

    return { mnemonic, btcAddress, ethAddress };
}

// Check Wallet for Balances
async function checkWallet() {
    const { mnemonic, btcAddress, ethAddress } = generateWallet();
    const btcBalance = await getBTCBalance(btcAddress);
    const ethBalance = await getETHBalance(ethAddress);

    totalGenerated++;

    if (btcBalance > 0.000000001 || ethBalance > 0.000000001) {
        const message = `🔹 Wallet Found!\n🔑 Mnemonic: ${mnemonic}\n\n💰 BTC: ${btcBalance}\n📍 BTC Address: ${btcAddress}\n\n💰 ETH: ${ethBalance}\n📍 ETH Address: ${ethAddress}`;
        bot.sendMessage(TELEGRAM_CHAT_ID, message);
        console.log("🚀 Wallet with balance found and sent to Telegram!");
    }
}

// Multi-threaded Execution
if (isMainThread) {
    console.log(`🚀 Starting ${MAX_WORKERS} workers...`);

    for (let i = 0; i < MAX_WORKERS; i++) {
        const worker = new Worker(__filename);
        worker.on('message', msg => console.log(msg));
        worker.on('error', err => console.error(`Worker Error: ${err.message}`));
    }

    setInterval(() => {
        bot.sendMessage(TELEGRAM_CHAT_ID, `🔥 Total Wallets Generated: ${totalGenerated}`);
    }, 300000); // Every 5 minutes
} else {
    setInterval(checkWallet, 500);
}
