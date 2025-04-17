<h1 align="center">Ethernal Bridges - Web Test Suite</h1>

<p align="center">
   <img src="./images/bridges.png" alt="Ethernal Bridges"/>
</p>

![Python Version](https://img.shields.io/badge/Python-3.9.x-4285f4?logo=python&logoColor=white)
![Google Chrome For Testnet Version](https://img.shields.io/badge/Google%20Chrome%20For%20Testing-130.0.6723.59-4285f4?logo=GoogleChrome&logoColor=white)
![Selenium](https://img.shields.io/badge/Selenium-4.25.0-4285f4?logo=selenium&logoColor=white)
![Metamask Wallet Supported](https://img.shields.io/badge/MetaMask%20Wallet-12.4.2-4285f4?logo=Ethereum&logoColor=white)
![Eternl Wallet Supported](https://img.shields.io/badge/Eternl%20Wallet-2.0.5.6-4285f4?logo=Cardano&logoColor=white)
![Eternl Beta Wallet Supported](https://img.shields.io/badge/Eternl%20Beta%20Wallet-2.0.3.15-4285f4?logo=Cardano&logoColor=white)
![macOS Support](https://img.shields.io/badge/macOS-tested-4ccf50?logo=macos&logoColor=white)
![Ubuntu Support](https://img.shields.io/badge/Ubuntu-not%20tested-ee0000?logo=ubuntu&logoColor=white)
![Windows Support](https://img.shields.io/badge/Windows-not%20tested-ee0000?logo=windows&logoColor=white)
![Cardano Privew Facut](https://github.com/bane/apex-fusion-reactor-test-suite/actions/workflows/cardano-faucet.yml/badge.svg)
![Multiple Reactor Internal Transactions](https://github.com/bane/apex-fusion-reactor-test-suite/actions/workflows/multiple-reactor-internal-transactions.yml/badge.svg)
![Multiple Reactor Partner Transactions](https://github.com/bane/apex-fusion-reactor-test-suite/actions/workflows/multiple-reactor-partner-transactions.yml/badge.svg)
![Multiple Skyline Internal Transactions](https://github.com/bane/apex-fusion-reactor-test-suite/actions/workflows/multiple-skyline-internal-transactions.yml/badge.svg)
![Single Transaction](https://github.com/bane/apex-fusion-reactor-test-suite/actions/workflows/single-transaction.yml/badge.svg)

An automated testing suite for the **Reactor** and **Skyline** websites, 
developed with **Selenium** and utilizing Chrome, 
is designed to thoroughly test every interaction and feature, 
including support for **MetaMask** and **Eternl** wallets. 
This tool mimics user behavior and checks responses to guarantee optimal performance and reliability. 
By addressing **all possible scenarios**, this tool provides a strong foundation for identifying and fixing potential issues in the website's functionality and user interface.

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/bane/apex-fusion-reactor-test-suite.git
   cd apex-fusion-reactor-test-suite
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
    SIGN_KEY=
    PRIME_WALLET_RECOVERY_PHRASE=
    VECTOR_WALLET_RECOVERY_PHRASE=
    NEXUS_WALLET_RECOVERY_PHRASE=
    PREVIEW_WALLET_RECOVERY_PHRASE=
    NEXUS_NETWORK_NAME=
    NEXUS_NETWORK_RPC_URL=
    NEXUS_NETWORK_CHAIN_ID=
    NEXUS_NETWORK_CURRENCY_SYMBOL=
    PARTNER_REACTOR_URL=
    INTERNAL_REACTOR_URL=
    INTERNAL_SKYLINE_URL=
    APEX_FUSION_FAUCET_URL=
   ```

## Usage Examples

### Reactor

1. **Prime to Vector**

   ```bash
   dotenv -f environment.env run -- python main.py Reactor Internal Prime 5 APEX Vector APEX
   ```

2. **Prime to Nexus**

   ```bash
   dotenv -f environment.env run -- python main.py Reactor Internal Prime 5 APEX Nexus APEX
   ```

3. **Vector to Prime**

   ```bash
   dotenv -f environment.env run -- python main.py Reactor Internal Vector 2 APEX Prime APEX
   ```
  
4. **Nexus to Prime**

   ```bash
   dotenv -f environment.env run -- python main.py Reactor Internal Nexus 2 APEX Prime APEX
   ```

### Skyline

1. **Prime (APEX) to Preview (WAPEX)**

   ```bash
   dotenv -f environment.env run -- python main.py Skyline Internal Prime 5 APEX Preview WAPEX
   ```

2. **Preview (Ada) to Prime (WAda)**

   ```bash
   dotenv -f environment.env run -- python main.py Skyline Internal Preview 5 Ada Prime WAda
   ```

3. **Prime (WAda) to Preview (Ada)**

   ```bash
   dotenv -f environment.env run -- python main.py Skyline Internal Prime 5 WAda Preview Ada
   ```

4. **Preview (WAPEX) to Prime (APEX)**

   ```bash
   dotenv -f environment.env run -- python main.py Skyline Internal Preview 5 WAPEX Prime APEX
   ```
