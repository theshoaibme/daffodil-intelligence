from .base import BaseAgent
from typing import Optional, Dict, List
import logging

logger = logging.getLogger(__name__)


class FeeAgent(BaseAgent):
    name = "Fee Agent"
    description = "Handles tuition fees, payments, scholarships, waivers, and financial matters"
    tools = ["calculate_fee", "get_payment_status", "get_scholarships", "apply_waiver", "get_installment_info"]

    SYSTEM_PROMPT = """You are the Fee Agent for DI (Daffodil Intelligence).
You help students with:
- Tuition fee calculation
- Payment status and history
- Scholarship information
- Waiver applications
- Installment plans
- Payment methods

Be clear about deadlines and amounts. Use tools for accurate calculations."""

    async def process(self, message: str, context: Optional[Dict] = None) -> str:
        message_lower = message.lower()

        if any(k in message_lower for k in ["fee", "tuition", "payment", "cost"]):
            return await self.handle_fee(context)

        elif any(k in message_lower for k in ["scholarship", "waiver", "discount"]):
            return await self.handle_scholarship()

        elif any(k in message_lower for k in ["payment", "due", "pay"]):
            return await self.handle_payment_status(context)

        elif any(k in message_lower for k in ["installment", "EMI", "partial"]):
            return await self.handle_installment()

        elif any(k in message_lower for k in ["scholarship", "apply", "eligibility"]):
            return await self.handle_apply_scholarship()

        return await self.generate_response(self.SYSTEM_PROMPT, message)

    async def handle_fee(self, context: Optional[Dict] = None) -> str:
        user_id = context.get("user_id", 1) if context else 1

        return f"""💰 **Your Tuition Fee**

**Spring 2026 Semester:**
- Tuition: 85,000 BDT
- Lab Fee: 5,000 BDT
- Exam Fee: 3,000 BDT
- Library Fee: 2,000 BDT
- **Total: 95,000 BDT**

**Previous Balance:** 0 BDT
**Total Payable: 95,000 BDT**

📅 Payment Deadline: May 25, 2026

**Payment Methods:**
- 💳 Mobile Banking (bKash, Nagad)
- 🏦 Bank Transfer
- 💵 Direct Payment at Accounts Office"""

    async def handle_scholarship(self) -> str:
        return """🎓 **Scholarships & Waivers**

**Available Scholarships:**

1. **Merit Scholarship**
   - Requirement: CGPA 3.9+
   - Waiver: 100% tuition
   - Apply: Semester start

2. **Vice Chancellor Scholarship**
   - Requirement: CGPA 3.75+
   - Waiver: 75% tuition
   - Limited seats: 50

3. **Financial Need Scholarship**
   - Requirement: Income certificate
   - Waiver: 50-100%
   - Apply: Throughout year

4. **Sibling Discount**
   - Waiver: 10% for second sibling
   - Apply: Admissions office

5. **Alumni Children**
   - Waiver: 15% tuition
   - Apply: Submit alumni ID"""

    async def handle_payment_status(self, context: Optional[Dict] = None) -> str:
        user_id = context.get("user_id", 1) if context else 1

        return f"""💳 **Payment Status**

**Student ID:** STU{user_id:05d}

| Semester | Amount | Paid | Due | Status |
|----------|--------|------|-----|--------|
| Fall 2025 | 95,000 | 95,000 | 0 | ✅ Paid |
| Spring 2026 | 95,000 | 47,500 | 47,500 | ⚠️ Due |

**Due Amount: 47,500 BDT**
📅 Deadline: May 25, 2026

**Last Payment:**
- Date: March 15, 2026
- Amount: 47,500 BDT
- Method: bKash

📝 Next installment due now!"""

    async def handle_installment(self) -> str:
        return """📊 **Installment Plan**

**Available Options:**

**Option A: 2 Installments**
- 1st: 50% before classes
- 2nd: 50% before midterm
- Interest: None

**Option B: 3 Installments**
- 1st: 40% before classes
- 2nd: 30% before midterm
- 3rd: 30% before final
- Interest: None

**Option C: 4 Installments**
- Monthly basis
- Interest: 5% (for delays)

**To Apply:**
📱 Student Portal > Finance > Installment
📍 Accounts Office

⚠️ Installment facility requires valid guarantor."""

    async def handle_apply_scholarship(self) -> str:
        return """📝 **Apply for Scholarship/Waiver**

**Steps:**

1. **Download Form**
   - Website: diu.edu.bd/scholarship
   - Student Portal

2. **Fill Details**
   - Personal info
   - Academic records
   - Income certificate (if need-based)

3. **Attach Documents**
   - Photo
   - Marksheets
   - Income proof
   - Guardian's NID

4. **Submit**
   - Online: scholarship@diu.edu.bd
   - Offline: Accounts Office

**Deadline:** Within first 2 weeks of semester

**Result:** Within 30 days of application

📞 Helpline: 02-xxxxxxx"""


async def calculate_fee(student_id: str, semester: str) -> Dict:
    return {
        "tuition": 85000,
        "lab_fee": 5000,
        "exam_fee": 3000,
        "library_fee": 2000,
        "total": 95000
    }


async def get_payment_status(student_id: str) -> Dict:
    return {
        "total_due": 47500,
        "paid": 47500,
        "pending": 47500,
        "last_payment_date": "2026-03-15"
    }


async def get_scholarships() -> List[Dict]:
    return [
        {"name": "Merit", "waiver": "100%", "cgpa": 3.9},
        {"name": "VC Scholarship", "waiver": "75%", "cgpa": 3.75},
        {"name": "Financial Need", "waiver": "50-100%", "cgpa": 2.5},
    ]


async def apply_waiver(student_id: str, waiver_type: str, documents: List[str]) -> Dict:
    return {
        "application_id": f"WVR-{hash(waiver_type) % 10000}",
        "status": "pending",
        "message": "Application submitted. Result in 30 days."
    }


async def get_installment_info(student_id: str) -> Dict:
    return {
        "available": True,
        "options": ["2 installments", "3 installments", "4 installments"],
        "interest_free": True
    }