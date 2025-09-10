# Trade Entry Indicator

## Description

**Trade Entry Indicator** is a comprehensive platform designed to monitor Binance exchange in real-time. The platform provides insights into various trading instruments across futures markets, signaling which instruments are optimal for short or long positions. With its advanced analytics and integration with Binance, Trade Entry Indicator is an essential tool for traders looking to maximize their market opportunities.

## Prerequisites

Before you begin, ensure you have met the following requirements:

- **Python 3.10.13 or higher**: The project requires Python 3.10.13+.
- **Conda** (recommended): To manage the environment and dependencies efficiently.
- **Pip**: Ensure you have `pip` installed for installing required Python packages.

## Installation

### 1. Clone the Repository
First, clone the repository to your local machine:

```bash
git clone https://github.com/stanislav-zhurylo/trade-entry-indicator.git
cd trade-entry-indicator
```

### 2. Create a Conda Environment (Recommended)
Create and activate a new Conda environment:

```bash
conda create -n tei-env python=3.10.13
conda activate tei-env
```

### 3. Install Dependencies
Install the required Python packages using `pip`:

```bash
pip install -e .
```
This will install all the dependencies listed in the setup.py file.

### 4. (Optional) Install Additional System Dependencies
Some system-level packages (like libffi, openssl, etc.) might need to be installed manually depending on your operating system. Ensure these dependencies are installed to avoid runtime issues.

## Running the Application
After installation, you can start the application by running the following command:

```bash
trade-entry-indicator
```

This command will start the platform, connect to Binance, and begin monitoring the instruments. The application will provide real-time signals for potential short or long opportunities.