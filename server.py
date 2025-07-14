#!/usr/bin/env python3

import os
import json
import sys
from typing import Any
from dotenv import load_dotenv
import httpx
from web3 import Web3
from eth_account import Account
from mcp.server.fastmcp import FastMCP

# Load environment
load_dotenv()

# Configuration
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
PAID_URL = os.getenv("PAID_URL", "http://localhost:4021/weather")
RECIPIENT_WALLET = os.getenv("RECIPIENT_WALLET")
PAYMENT_AMOUNT = float(os.getenv("PAYMENT_AMOUNT"))

# Setup blockchain
w3 = Web3(Web3.HTTPProvider('https://sepolia.base.org'))
account = Account.from_key(PRIVATE_KEY)

# Create MCP server
mcp = FastMCP("x402-eth-payment")

async def pay_and_retry_eth(url: str, params: dict = None) -> dict[str, Any]:
    """Handle HTTP 402 payment flow using ETH"""
    
    print(f"[PAYMENT] Starting payment flow for {url}", file=sys.stderr)
    if params:
        param_str = "&".join([f"{k}={v}" for k, v in params.items()])
        print(f"[PAYMENT] Request parameters: {param_str}", file=sys.stderr)
    
    async with httpx.AsyncClient() as client:
        # Initial request
        response = await client.get(url, params=params)
        print(f"[HTTP] Response status: {response.status_code}", file=sys.stderr)
        
        if response.status_code != 402:
            print("[PAYMENT] No payment required, request successful", file=sys.stderr)
            return {"data": response.json(), "paid": False}
        
        # Use configured payment details
        amount_eth = PAYMENT_AMOUNT
        recipient = RECIPIENT_WALLET
        
        print(f"[PAYMENT] 402 Payment Required - {amount_eth} ETH to {recipient}", file=sys.stderr)
        
        # Real ETH payment
        try:
            # Check ETH balance
            eth_balance = w3.eth.get_balance(account.address)
            eth_balance_ether = eth_balance / 10**18
            
            # Calculate amounts
            amount_wei = int(amount_eth * 10**18)  # Convert ETH to wei
            gas_limit = 21000  # Standard ETH transfer
            gas_price = max(1_000_000_000, w3.eth.gas_price // 2)  # At least 1 gwei
            gas_cost = gas_limit * gas_price
            total_cost = amount_wei + gas_cost
            
            print(f"[WALLET] Balance: {eth_balance_ether:.6f} ETH, Cost: {total_cost / 10**18:.6f} ETH", file=sys.stderr)
            
            if eth_balance < total_cost:
                print("[ERROR] Insufficient balance for transaction", file=sys.stderr)
                raise Exception(f"Insufficient ETH. Need {total_cost / 10**18:.6f} ETH, have {eth_balance_ether:.6f} ETH")
            
            # Build simple ETH transfer transaction
            nonce = w3.eth.get_transaction_count(account.address)
            tx = {
                'to': recipient,
                'value': amount_wei,
                'gas': gas_limit,
                'gasPrice': gas_price,
                'nonce': nonce,
            }
            
            # Sign and send transaction
            signed_txn = account.sign_transaction(tx)
            print(f"[BLOCKCHAIN] Transaction signed, nonce: {nonce}", file=sys.stderr)
            
            # Get raw transaction data
            raw_tx = None
            for attr_name in ['raw_transaction', 'rawTransaction', 'data']:
                if hasattr(signed_txn, attr_name):
                    raw_data = getattr(signed_txn, attr_name)
                    # Ensure it's bytes-like
                    if hasattr(raw_data, 'hex'):
                        raw_tx = raw_data
                        break
                    elif isinstance(raw_data, (bytes, bytearray)):
                        raw_tx = raw_data
                        break
                    elif isinstance(raw_data, str) and raw_data.startswith('0x'):
                        raw_tx = bytes.fromhex(raw_data[2:])
                        break
            
            if raw_tx is None:
                available_attrs = [attr for attr in dir(signed_txn) if not attr.startswith('_')]
                print("[ERROR] Could not extract raw transaction data", file=sys.stderr)
                raise Exception(f"Could not find raw transaction data. Available attributes: {available_attrs}")
            
            # Send transaction
            tx_hash = w3.eth.send_raw_transaction(raw_tx).hex()
            print(f"[BLOCKCHAIN] Transaction broadcast: {tx_hash}", file=sys.stderr)
            
            # Wait for confirmation
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            
            if receipt.status == 1:
                actual_gas_used = receipt.gasUsed
                actual_cost = (amount_wei + actual_gas_used * gas_price) / 10**18
                print(f"[BLOCKCHAIN] Transaction confirmed in block {receipt.blockNumber}, cost: {actual_cost:.6f} ETH", file=sys.stderr)
            else:
                print("[ERROR] Transaction failed on blockchain", file=sys.stderr)
                raise Exception("Transaction failed")
                
        except Exception as e:
            print(f"[ERROR] Payment processing failed: {str(e)}", file=sys.stderr)
            raise
        
        # Retry with payment proof
        paid_response = await client.get(url, params=params, headers={"payment-tx-hash": tx_hash})
        
        if paid_response.status_code == 200:
            print("[PAYMENT] Payment verified, data retrieved successfully", file=sys.stderr)
            return {"data": paid_response.json(), "paid": True, "tx_hash": tx_hash, "payment_type": "ETH"}
        else:
            print(f"[ERROR] Payment verification failed with status {paid_response.status_code}", file=sys.stderr)
            raise Exception(f"Payment verification failed: {paid_response.status_code}")

@mcp.tool()
async def get_weather(location: str = "London") -> str:
    """Get weather data with automatic ETH payment
    
    Args:
        location: Location to get weather for (city name, coordinates, zip code, etc.)
    """
    print(f"[TOOL] get_weather called for location: {location}", file=sys.stderr)
    try:
        params = {"location": location}
        result = await pay_and_retry_eth(PAID_URL, params)
        print(f"[TOOL] Weather data retrieved successfully for {location}", file=sys.stderr)
        return json.dumps(result, indent=2)
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        print(f"[ERROR] Weather tool failed for {location}: {error_msg}", file=sys.stderr)
        return error_msg

@mcp.tool()
async def check_balance() -> str:
    """Check wallet ETH balance"""
    try:
        balance = w3.eth.get_balance(account.address) / 10**18
        nonce = w3.eth.get_transaction_count(account.address)
        
        # Estimate how many transactions possible
        gas_cost = 21000 * 1_000_000_000  # 21k gas at 1 gwei
        payment_cost = 0.0001 * 10**18  # 0.0001 ETH payment
        total_per_tx = (gas_cost + payment_cost) / 10**18
        possible_txs = int(balance / total_per_tx) if total_per_tx > 0 else 0
        
        return f"""Wallet: {account.address}
ETH Balance: {balance:.6f} ETH
Nonce: {nonce}
Estimated transactions possible: {possible_txs}
Cost per transaction: ~{total_per_tx:.6f} ETH"""
    except Exception as e:
        return f"Error: {e}"

@mcp.tool()
async def check_transaction_signing() -> str:
    """Test transaction signing to debug the rawTransaction issue"""
    try:
        # Create test transaction
        test_tx = {
            'to': account.address,
            'value': 0,
            'gas': 21000,
            'gasPrice': 1000000000,
            'nonce': w3.eth.get_transaction_count(account.address),
        }
        
        # Test signing
        signed = account.sign_transaction(test_tx)
        
        # Check what attributes exist
        attrs = [attr for attr in dir(signed) if not attr.startswith('_')]
        
        result = {
            "signing_method": "account.sign_transaction",
            "transaction_type": str(type(signed)),
            "available_attributes": attrs,
            "has_rawTransaction": hasattr(signed, 'rawTransaction'),
            "has_raw_transaction": hasattr(signed, 'raw_transaction'),
        }
        
        # Try to access the raw transaction
        raw_tx = None
        found_attr = None
        for attr in ['raw_transaction', 'rawTransaction', 'data']:
            if hasattr(signed, attr):
                raw_tx = getattr(signed, attr)
                found_attr = attr
                break
        
        if raw_tx is not None:
            result[f"{found_attr}_type"] = str(type(raw_tx))
            result["status"] = f"✅ {found_attr} attribute found"
        else:
            result["status"] = "❌ No raw transaction attribute found"
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        return f"Transaction signing test failed: {str(e)}"

if __name__ == "__main__":
    print("[SERVER] x402 ETH Payment Server starting", file=sys.stderr)
    print(f"[CONFIG] Wallet: {account.address}", file=sys.stderr)
    print(f"[CONFIG] Target URL: {PAID_URL}", file=sys.stderr)
    print(f"[CONFIG] Payment: {PAYMENT_AMOUNT} ETH to {RECIPIENT_WALLET}", file=sys.stderr)
    print(f"[CONFIG] Network: Base Sepolia", file=sys.stderr)
    print("[SERVER] Ready for payment requests", file=sys.stderr)
    mcp.run(transport='stdio')