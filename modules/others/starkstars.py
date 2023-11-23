from utils.tools import repeater, gas_checker
from modules import Minter
from config import TOKENS_PER_CHAIN, STARKSTARS_COUNTACTS
from settings import STARKSTARS_NFT_CONTRACTS, USE_PROXY


class StarkStars(Minter):
    def __init__(self, client):
        self.client = client

    async def get_new_nft_id(self):
        for contract_id, contract_address in STARKSTARS_COUNTACTS.items():
            if contract_id in STARKSTARS_NFT_CONTRACTS:
                nft_contract = await self.client.get_contract(contract_address=contract_address)
                if not (await nft_contract.functions["balance_of"].call(self.client.address))[0]:
                    return contract_id
        raise RuntimeError('All StarkStars NFT have been minted')

    @repeater
    @gas_checker
    async def mint(self):
        try:
            await self.client.initialize_account()

            eth_contract = TOKENS_PER_CHAIN[self.client.network.name]["ETH"]

            contact_id = await self.get_new_nft_id()

            nft_contract = await self.client.get_contract(contract_address=STARKSTARS_COUNTACTS[contact_id])

            self.client.logger.info(f"{self.client.info} Mint StarkStars#00{contact_id:0>2} NFT")

            mint_price = (await nft_contract.functions["get_price"].call())[0]

            approve_call = self.client.get_approve_call(eth_contract, nft_contract.address, mint_price)

            mint_call = nft_contract.functions["mint"].prepare()

            return await self.client.send_transaction(approve_call, mint_call)
        finally:
            if USE_PROXY:
                await self.client.session.close()