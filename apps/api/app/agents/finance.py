from .base import BaseAgent
from typing import Optional, Dict


class FinanceAgent(BaseAgent):
    name = "Finance Agent"
    description = "Handles tuition fees, payments, waivers, scholarships, and financial queries"
    tools = ["get_fee_structure", "check_dues", "apply_waiver", "get_scholarships", "payment_history"]

    SYSTEM_PROMPT = """You are the Finance Agent for DI.
You help with:
- Tuition and fee information
- Payment status and history
- Scholarship applications
- Fee waiver requests
- Financial aid information"""

    async def process(self, message: str, context: Optional[Dict] = None) -> str:
        message_lower = message.lower()

        if any(k in message_lower for k in ["fee", "tuition", "cost"]):
            return await self.handle_fees()

        elif any(k in message_lower for k in ["due", "pending", "payment"]):
            return await self.handle_dues(context)

        elif any(k in message_lower for k in ["scholarship", "waiver"]):
            return await self.handle_scholarships()

        return await self.generate_response(self.SYSTEM_PROMPT, message)

    async def handle_fees(self) -> str:
        fees = await get_fee_structure()
        return f"""💰 **Fee Structure**

- Per Credit: ৳{fees['per_credit']}
- Per Semester: ৳{fees['per_semester']}
- Lab Fees: ৳{fees['lab_fees']}
- Registration: ৳{fees['registration']}

Contact the finance office for details."""

    async def handle_dues(self, context: Optional[Dict]) -> str:
        user_id = context.get("user_id", 1) if context else 1
        dues = await check_dues(user_id)
        return f"""📋 **Payment Status**

- Total Due: ৳{dues['total_due']}
- Paid: ৳{dues['paid']}
- Pending: ৳{dues['pending']}
- Due Date: {dues['due_date']}

Clear pending dues to avoid late fees."""

    async def handle_scholarships(self) -> str:
        scholarships = await get_scholarships()
        sch_list = "\n".join([f"- **{s['name']}**: ৳{s['amount']} (Deadline: {s['deadline']})" for s in scholarships])
        return f"""🎓 **Scholarships**

{sch_list}

Apply through the scholarship portal."""


async def get_fee_structure() -> dict:
    return {"per_credit": 5000, "per_semester": 15000, "lab_fees": 2000, "registration": 1000}


async def check_dues(user_id: int) -> dict:
    return {"total_due": 25000, "paid": 15000, "pending": 10000, "due_date": "2024-04-15"}


async def get_scholarships() -> list[dict]:
    return [
        {"name": "Merit Scholarship", "amount": 20000, "deadline": "2024-03-31"},
        {"name": "Financial Aid", "amount": 15000, "deadline": "2024-04-15"},
    ]