# services/pricing.py
from decimal import Decimal
from config.database import SessionLocal
from models.schemas import SystemSettings

class POSProcessor:
    SERVICES = {
        'self_8': ('Self-Service Wash & Dry (8kg)', Decimal('145.00'), Decimal('8')),
        'self_13': ('Self-Service Wash & Dry (13kg)', Decimal('240.00'), Decimal('13')),
        'classic': ('Drop-Off Classic (8kg)', Decimal('130.00'), Decimal('8')),
        'saver': ('Drop-Off Saver (8kg)', Decimal('160.00'), Decimal('8')),
        'signature': ('Drop-Off Signature (8kg)', Decimal('200.00'), Decimal('8')),
        'premium': ('Drop-Off Premium (8kg)', Decimal('260.00'), Decimal('8')),
    }
    ADDONS = {
        'superwash_self': ('Superwash Self-Service', Decimal('105.00')),
        'superwash_dropoff': ('Superwash Drop-Off', Decimal('35.00')),
        'fold': ('Fold', Decimal('40.00')),
        'sort': ('Sort', Decimal('30.00')),
        'add_dry': ('Add Dry', Decimal('70.00')),
        'delivery': ('Delivery', Decimal('100.00')),
        'rush_24h': ('Drop-Off Service Charge (24 hrs)', Decimal('120.00')),
        'rush_2days': ('Drop-Off Service Charge (2 days)', Decimal('70.00')),
    }

    @classmethod
    def calculate_service_total(cls, service_code, weight_input, addon_codes=None):
        if service_code not in cls.SERVICES:
            return {'success': False, 'message': 'Select a valid laundry service.'}
        label, base_price, max_weight = cls.SERVICES[service_code]
        # Bundle pricing is fixed by the selected capacity. A blank POS weight is
        # treated as a full bundle instead of rejecting a valid walk-in sale.
        try:
            weight = Decimal(str(weight_input)) if weight_input not in (None, '') else max_weight
        except Exception:
            return {'success': False, 'message': 'Enter a valid load weight.'}
        if weight <= 0 or weight > max_weight:
            return {'success': False, 'message': f'{label} accepts loads from 0.1kg to {max_weight}kg.'}
        addon_codes = addon_codes or []
        if any(code not in cls.ADDONS for code in addon_codes):
            return {'success': False, 'message': 'An invalid add-on was selected.'}
        addons_total = sum((cls.ADDONS[code][1] for code in addon_codes), Decimal('0.00'))
        return {'success': True, 'weight': float(weight), 'total_amount': float(base_price + addons_total),
                'service_label': label, 'addons': [cls.ADDONS[code][0] for code in addon_codes]}
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
