# services/pricing.py
from decimal import Decimal
from config.database import SessionLocal
from models.schemas import SystemSettings

class POSProcessor:
    @staticmethod
    def validate_and_calculate(weight_input):
        """
        Validates the input laundry weight against system constraints
        and calculates the total cost using dynamic rates from the database.
        """
        db = SessionLocal()
        try:
            # 1. Fetch dynamic global settings from the database
            settings = db.query(SystemSettings).first()
            
            # Fallback values if tbl_system_settings is completely empty
            price_per_kg = Decimal(str(settings.price_per_kg)) if settings else Decimal('65.00')
            max_limit = settings.max_weight_limit_kg if settings else 8
            
            # 2. Convert raw input string/float safely to Decimal
            weight = Decimal(str(weight_input))
            
            # 3. Enforce business rule: Max 8kg limit check
            if weight > max_limit:
                return {
                    "success": False, 
                    "message": f"Transaction rejected. Weight exceeds the maximum allowed limit of {max_limit}kg per load."
                }
            
            if weight <= 0:
                return {
                    "success": False, 
                    "message": "Transaction rejected. Weight must be greater than 0kg."
                }
            
            # 4. Calculate total amount (Weight * Price per Kg)
            total_amount = weight * price_per_kg
            
            return {
                "success": True,
                "weight": float(weight),
                "total_amount": float(total_amount),
                "message": "Validation passed."
            }
            
        finally:
            db.close()