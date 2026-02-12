import asyncio
from payos import PayOS
from payos.type import PaymentData, ItemData
from app.core.config import settings

class PayOSService:
    def __init__(self):
        self.payos = PayOS(
            client_id=settings.PAYOS_CLIENT_ID,
            api_key=settings.PAYOS_API_KEY,
            checksum_key=settings.PAYOS_CHECKSUM_KEY
        )

    async def create_payment_link(self, order_code: int, amount: int, description: str, return_url: str, cancel_url: str) -> dict:
        """
        Create a payment link using PayOS.
        Runs the synchronous PayOS call in a thread pool.
        """
        # Create ItemData
        # Description is strictly limited in length by PayOS, so truncate if needed
        item = ItemData(name=description[:50], quantity=1, price=amount)

        # Create PaymentData object
        # Ensure returnUrl/cancelUrl are absolute URLs
        base_domain = getattr(settings, "DOMAIN", "http://localhost:5000")
        
        # If return_url already starts with http, use it, else prepend domain
        full_return_url = return_url if return_url.startswith("http") else f"{base_domain}{return_url}"
        full_cancel_url = cancel_url if cancel_url.startswith("http") else f"{base_domain}{cancel_url}"

        payment_data = PaymentData(
            orderCode=order_code,
            amount=amount,
            description=description[:25], # PayOS desc limit is short
            items=[item],
            returnUrl=full_return_url,
            cancelUrl=full_cancel_url
        )

        try:
            loop = asyncio.get_running_loop()
            payos_create_link = await loop.run_in_executor(
                None, 
                self.payos.createPaymentLink, 
                payment_data
            )
            
            # PayOS returns CreatePaymentResult object
            return {
                "checkoutUrl": payos_create_link.checkoutUrl,
                "qrCode": payos_create_link.qrCode,
                "orderCode": payos_create_link.orderCode,
                "status": payos_create_link.status
            }
        except Exception as e:
            print(f"❌ PayOS API Error: {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()
            raise e

    async def get_payment_info(self, order_code: int):
        try:
            loop = asyncio.get_running_loop()
            payment_info = await loop.run_in_executor(
                None,
                self.payos.getPaymentLinkInformation,
                order_code
            )
            return payment_info
        except Exception as e:
            print(f"❌ PayOS Info Error: {str(e)}")
            raise e
