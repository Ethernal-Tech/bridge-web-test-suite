<h1 align="center">BRIDGE WEB TEST SUITE</h1>

<p align="center">
   <img src="./images/bridges.png" alt="Ethernal Bridges"/>
</p>

![Python Version](https://img.shields.io/badge/Python-3.9.x-4285f4?logo=python&logoColor=white)
![Google Chrome For Testnet Version](https://img.shields.io/badge/Google%20Chrome%20For%20Testing-139.0.7258.129-4285f4?logo=GoogleChrome&logoColor=white)
![Selenium](https://img.shields.io/badge/Selenium-4.34.0-4285f4?logo=selenium&logoColor=white)
![Metamask Wallet Supported](https://img.shields.io/badge/MetaMask%20Wallet-13.0.1-4285f4?logo=Ethereum&logoColor=white)
![Eternl Wallet Supported](https://img.shields.io/badge/Eternl%20Wallet-2.0.11.2-4285f4?logo=Cardano&logoColor=white)
![macOS Support](https://img.shields.io/badge/macOS-tested-4ccf50?logo=macos&logoColor=white)
![Ubuntu Support](https://img.shields.io/badge/Ubuntu-not%20tested-ee0000?logo=ubuntu&logoColor=white)
![Windows Support](https://img.shields.io/badge/Windows-not%20tested-ee0000?logo=windows&logoColor=white)
![Cardano Privew Facut](https://github.com/Ethernal-Tech/bridge-web-test-suite/actions/workflows/cardano-faucet.yml/badge.svg)
![Multiple Reactor Partner Transactions](https://github.com/Ethernal-Tech/bridge-web-test-suite/actions/workflows/multiple-reactor-partner-transactions.yml/badge.svg)
![Multiple Skyline Partner Transactions](https://github.com/Ethernal-Tech/bridge-web-test-suite/actions/workflows/multiple-skyline-partner-transactions.yml/badge.svg)
![Single Transaction](https://github.com/Ethernal-Tech/bridge-web-test-suite/actions/workflows/single-transaction.yml/badge.svg)

An automated testing suite for the **Reactor Bridge** and **Skyline Bridge** websites, 
developed with **Selenium** and utilizing Chrome, 
is designed to thoroughly test every interaction and feature, 
including support for **MetaMask** and **Eternl** wallets. 
This tool mimics user behavior and checks responses to guarantee optimal performance and reliability. 
By addressing **all possible scenarios**, this tool provides a strong foundation for identifying and fixing potential issues in the website's functionality and user interface.

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/Ethernal-Tech/bridge-web-test-suite.git
   cd bridge-web-test-suite
   ```

2. Set up a virtual environment (recommended):

   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

3. Install the required packages:

   ```bash
   pip install -r requirements.txt
   ```

## Configuration

1. Copy the example configuration file:

   ```bash
   cp environment.env.example environment.env
   ```

2. Open `environment.env` and set environment variables:

   ```
   CHROME_CONFIGS_URL=''
   CHROMEDRIVER_VERSION=''
   BRIDGE_URL=''
   SIGN_KEY=''
   APEX_FUSION_FAUCET_URL=''
   PREVIEW_FAUCET_API_KEY=''
   PREPROD_FAUCET_API_KEY=''
   BRD_PROXY_USERNAME=''
   BRD_PROXY_PASSWORD=''
   CARDANO_TESTNET_WALLETS=''
   ```

## Usage Examples

### Reactor

1. **Prime to Nexus**

   ```bash
   dotenv -f environment.env run -- python main.py Reactor Prime 5 AP3X Nexus
   ```
 
2. **Nexus to Prime**

   ```bash
   dotenv -f environment.env run -- python main.py Reactor Nexus 5 AP3X Prime
   ```

### Skyline

1. **Prime (AP3X) to Preview (cAP3X)**

   ```bash
   dotenv -f environment.env run -- python main.py Skyline Prime 5 AP3X Preview
   ```

2. **Preview (cAP3X) to Prime (AP3X)**

   ```bash
   dotenv -f environment.env run -- python main.py Skyline Preview 5 cAP3X Prime
   ```
