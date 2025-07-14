# X402 Protocol Integration with Fetch.ai

This project demonstrates the integration of the X402 protocol (HTTP 402 Payment Required) with Fetch.ai's uAgents framework, enabling automatic cryptocurrency payments for accessing paid APIs and services.

## Overview

The X402 protocol extends HTTP with automatic payment capabilities, allowing clients to seamlessly pay for API access when they receive a 402 Payment Required response. This integration combines:

- **X402 Payment Protocol**: Automatic ETH payments for API access
- **Fetch.ai uAgents**: Decentralized agent framework for AI services
- **MCP (Model Control Protocol)**: Tool integration for AI assistants
- **FastAPI**: High-performance web framework for API endpoints

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   MCP Client    │    │   uAgent with   │    │   X402 Payment  │
│   (AI Assistant)│◄──►│   MCP Adapter   │◄──►│   Server        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │   ASI1 API      │    │   Weather API   │
                       │   (LLM Service) │    │   (Paid Service)│
                       └─────────────────┘    └─────────────────┘
                                                        │
                                                        ▼
                                              ┌─────────────────┐
                                              │   Blockchain    │
                                              │   (Base Sepolia)│
                                              └─────────────────┘
```

## Key Components

### 1. X402 Payment Server (`server.py`)
- Handles HTTP 402 Payment Required responses
- Processes ETH payments on Base Sepolia testnet
- Integrates with external weather API
- Provides MCP tools for AI assistants

### 2. uAgent with MCP Adapter (`agent.py`)
- Bridges MCP servers with Fetch.ai uAgents
- Enables communication via Agentverse mailbox
- Supports chat protocol for AI interactions
- Integrates with ASI1 API for LLM processing

### 3. FastAPI Payment Endpoint (`fastApi.py`)
- Simple weather API endpoint requiring payment
- Returns 402 status for unpaid requests
- Verifies payment via transaction hash
- Provides real weather data after payment

## Features

- **Automatic Payment Processing**: Seamless ETH payments for API access
- **Blockchain Integration**: Uses Base Sepolia testnet for transactions
- **MCP Tool Integration**: Exposes payment functionality to AI assistants
- **Agent Communication**: Supports Fetch.ai agent-to-agent messaging
- **Real-time Weather Data**: Paid access to weather information
- **Transaction Verification**: Blockchain-based payment proof

## Installation

### Prerequisites

- Python 3.11+
- Poetry (for dependency management)
- ETH wallet with Base Sepolia testnet funds
- WeatherAPI.com API key
- ASI1 API key

### Setup

1. **Clone and install dependencies:**
```bash
git clone <repository-url>
cd x402
poetry install
```

2. **Configure environment variables:**
```bash
cp .env.example .env
# Edit .env with your configuration:
# PRIVATE_KEY=your_eth_private_key
# RECIPIENT_WALLET=payment_recipient_address
# PAYMENT_AMOUNT=0.00000001
# WEATHER_API_KEY=your_weather_api_key
# PAID_URL=http://localhost:4021/weather
```

3. **Install uAgents adapter:**
```bash
cd uagents-adapter
poetry install
```

## Usage

### Running the Complete System

1. **Start the FastAPI weather server:**
```bash
poetry run python fastApi.py
```

2. **Start the X402 payment server with uAgent:**
```bash
poetry run python agent.py
```

3. **Test the payment flow:**
```bash
# The MCP server will be available via stdio
# Connect with an MCP-compatible client
```

### MCP Tools Available

- **`get_weather(location)`**: Get weather data with automatic payment
- **`check_balance()`**: Check wallet ETH balance and transaction capacity
- **`check_transaction_signing()`**: Debug transaction signing functionality

### Example Usage

```python
# Through MCP client
tools = await mcp_client.list_tools()
result = await mcp_client.call_tool("get_weather", {"location": "Tokyo"})
# Automatically handles 402 payment and returns weather data
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PRIVATE_KEY` | ETH private key for payments | Required |
| `RECIPIENT_WALLET` | Payment recipient address | Required |
| `PAYMENT_AMOUNT` | Payment amount in ETH | 0.00000001 |
| `WEATHER_API_KEY` | WeatherAPI.com key | Required |
| `PAID_URL` | Target API URL | http://localhost:4021/weather |

### Agent Configuration

```python
# In agent.py
mcp_adapter = MCPServerAdapter(
    mcp_server=mcp,
    asi1_api_key="your_asi1_api_key",
    model="asi1-mini"
)

agent = Agent(
    name="mcp_agent",
    port=8000,
    seed="mcp agent secret phrase",
    mailbox=True  # Enable Agentverse mailbox
)
```

## Payment Flow

1. **Initial Request**: Client requests weather data
2. **402 Response**: Server returns Payment Required with payment details
3. **Payment Processing**: Client automatically sends ETH payment
4. **Transaction Verification**: Payment confirmed on blockchain
5. **Data Delivery**: Weather data returned with payment proof

## Security Considerations

- Private keys are loaded from environment variables
- Payment amounts are configurable and minimal
- Transaction verification prevents double-spending
- All payments are recorded on blockchain for transparency

## Development

### Project Structure

```
x402/
├── agent.py              # uAgent with MCP adapter
├── server.py             # X402 payment server
├── fastApi.py            # Weather API endpoint
├── pyproject.toml        # Dependencies
└── uagents-adapter/      # MCP adapter package
    ├── src/
    │   └── uagents_adapter/
    │       ├── mcp/
    │       │   ├── adapter.py    # MCP server adapter
    │       │   └── protocol.py   # MCP protocol definitions
    │       └── ...
    └── pyproject.toml
```

### Running Tests

```bash
# Test wallet balance
poetry run python -c "from server import check_balance; print(check_balance())"

# Test transaction signing
poetry run python -c "from server import check_transaction_signing; print(check_transaction_signing())"
```

## Troubleshooting

### Common Issues

1. **Insufficient ETH Balance**
   - Ensure wallet has enough ETH for payment + gas fees
   - Check balance with `check_balance()` tool

2. **Transaction Signing Errors**
   - Verify private key format (with 0x prefix)
   - Test with `check_transaction_signing()` tool

3. **API Connection Issues**
   - Check weather API key validity
   - Verify network connectivity to Base Sepolia

### Debug Commands

```bash
# Check wallet status
poetry run python -c "from server import w3, account; print(f'Address: {account.address}'); print(f'Balance: {w3.eth.get_balance(account.address)/10**18} ETH')"

# Test weather API
curl "http://localhost:4021/weather?location=London"
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Resources

- [Fetch.ai uAgents Documentation](https://docs.fetch.ai/uAgents)
- [MCP Protocol Specification](https://modelcontextprotocol.io/)
- [Base Sepolia Testnet](https://base.org/docs/network-information)
- [WeatherAPI.com](https://www.weatherapi.com/)
- [ASI1 API Documentation](https://api.asi1.ai/)
