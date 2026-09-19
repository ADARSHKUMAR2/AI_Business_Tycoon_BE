"""
Game constants and enumerations.
"""

# ── Employee stat ranges ──────────────────────────────────────────────
EMPLOYEE_STAT_MIN = 1
EMPLOYEE_STAT_MAX = 100

# ── Employee level constants ──────────────────────────────────────────
EMPLOYEE_MAX_LEVEL      = 10
EMPLOYEE_XP_PER_LEVEL   = 100

# ── Business constants ────────────────────────────────────────────────
MAX_EMPLOYEES_PER_BUSINESS = 10
MAX_PRICE_MULTIPLIER       = 3.0
MIN_PRICE_MULTIPLIER       = 0.5

# ── Land constants ────────────────────────────────────────────────────
MAX_LAND_GRID_SIZE = 10  # 10x10 grid

# ── Customer constants ────────────────────────────────────────────────
CUSTOMER_MIN_PATIENCE = 10    # seconds
CUSTOMER_MAX_PATIENCE = 300   # seconds
CUSTOMER_MIN_BUDGET   = 50.0
CUSTOMER_MAX_BUDGET   = 500.0

# ── Economy constants ─────────────────────────────────────────────────
BASE_DAILY_RENT        = 500.0
BASE_DAILY_ELECTRICITY = 200.0

# ── Player progression ────────────────────────────────────────────────
PLAYER_MAX_LEVEL   = 100
PLAYER_XP_PER_LEVEL = 1000

# ── Phase 3: Cleanliness / Trash ──────────────────────────────────────
STORE_RATING_MAX          = 5.0   # Perfect store rating
STORE_RATING_MIN          = 0.0   # Worst store rating
STORE_RATING_TRASH_PENALTY = 0.1  # Rating lost per active trash item

# ── Phase 3: Shelf Upgrades ───────────────────────────────────────────
# Maps target max_stock capacity → cost in ₹
SHELF_UPGRADE_COSTS: dict[int, float] = {
    20: 2000.0,   # Upgrade from 10 → 20 slots costs ₹2,000
    30: 5000.0,   # Upgrade from 20 → 30 slots costs ₹5,000
}
SHELF_MAX_CAPACITY = 30  # Hard ceiling on shelf size

# ── Phase 3: Employee Stat Upgrades ──────────────────────────────────
# Cost = UPGRADE_COST_BASE * current_stat_value
# e.g. upgrading speed from 70 to 75 costs 5 * 70 * 10 = ₹3,500
UPGRADE_COST_BASE          = 10    # Rupees per existing stat point per upgrade point
UPGRADE_STAT_INCREMENT     = 5     # How many points each upgrade adds
UPGRADE_CARRY_CAP_INCREMENT = 2    # Carry capacity grows by 2 per upgrade
UPGRADE_SPEED_MAX          = 100   # Mirrors EMPLOYEE_STAT_MAX
UPGRADE_CARRY_MAX          = 20    # Hard ceiling on carry_capacity

# ── Indian names for random employee generation ───────────────────────
INDIAN_FIRST_NAMES = [
    "Ravi", "Priya", "Amit", "Anjali", "Vikram", "Neha", "Arjun", "Pooja",
    "Rahul", "Sneha", "Karan", "Divya", "Rohan", "Kavya", "Aditya", "Meera",
    "Sanjay", "Shreya", "Nitin", "Ananya", "Mohit", "Isha", "Varun", "Nisha"
]

INDIAN_LAST_NAMES = [
    "Kumar", "Singh", "Sharma", "Patel", "Reddy", "Mehta", "Gupta", "Joshi",
    "Verma", "Rao", "Nair", "Iyer", "Desai", "Shah", "Agarwal", "Pillai"
]
