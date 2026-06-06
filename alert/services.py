import requests


class CryptoPriceService:

    @staticmethod
    def get_live_crypto_price(crypto_symbol):

        symbol_map = {
            'BTC': 'bitcoin',
            'ETH': 'etherum',
            'SOL': 'solana'
        }

        coin_id = symbol_map.get(crypto_symbol.upper())

        if not coin_id:
            print(f'symbol {crypto_symbol} not in mapping')

            return None
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd"
        try:

            response = requests.get(url, timeout=5)

            if response.status_code == 200:
                data = response.json()

                live_price = data.get(coin_id, {}).get('usd')
                return float(live_price) if live_price else None
            else:
                print(f'CoinGeko responded with error {response.status_code}')

                return None
        except requests.RequestException as e:
            print(f'Connection error server fail {e}')
            return None
