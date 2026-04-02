"""
Viori Data Hub - SQLAlchemy Models
All table schemas matching the SQLite data hub, but Postgres-native.
"""
from sqlalchemy import (
    Column, Integer, Float, String, Text, Date, DateTime, Boolean,
    UniqueConstraint, Index, func, create_engine
)
from sqlalchemy.orm import declarative_base, sessionmaker
import os

Base = declarative_base()


# ============================================================
# PROFORMA TABLES
# ============================================================

class ProformaCashFlowMonthly(Base):
    __tablename__ = "proforma_cash_flow_monthly"
    id = Column(Integer, primary_key=True, autoincrement=True)
    period = Column(String(10), nullable=False)
    metric = Column(String(100), nullable=False)
    value = Column(Float, nullable=False)
    __table_args__ = (UniqueConstraint("period", "metric"),)


class ProformaExpensesMonthly(Base):
    __tablename__ = "proforma_expenses_monthly"
    id = Column(Integer, primary_key=True, autoincrement=True)
    period = Column(String(10), nullable=False)
    category = Column(String(200), nullable=False)
    value = Column(Float, nullable=False)
    __table_args__ = (UniqueConstraint("period", "category"),)


class ProformaSkuMonthly(Base):
    __tablename__ = "proforma_sku_monthly"
    id = Column(Integer, primary_key=True, autoincrement=True)
    period = Column(String(10), nullable=False)
    sku = Column(String(50), nullable=False)
    orders = Column(Integer, nullable=False)
    __table_args__ = (UniqueConstraint("period", "sku"),)


class ProformaRdataMonthly(Base):
    __tablename__ = "proforma_rdata_monthly"
    id = Column(Integer, primary_key=True, autoincrement=True)
    period = Column(String(10), nullable=False)
    metric = Column(String(100), nullable=False)
    value = Column(Float, nullable=False)
    __table_args__ = (UniqueConstraint("period", "metric"),)


class ProformaContractorsMonthly(Base):
    __tablename__ = "proforma_contractors_monthly"
    id = Column(Integer, primary_key=True, autoincrement=True)
    period = Column(String(10), nullable=False)
    department = Column(String(100), nullable=False)
    value = Column(Float, nullable=False)
    __table_args__ = (UniqueConstraint("period", "department"),)


class ProformaContractorsDetail(Base):
    __tablename__ = "proforma_contractors_detail"
    id = Column(Integer, primary_key=True, autoincrement=True)
    contractor_id = Column(Integer)
    name = Column(String(200), nullable=False)
    title = Column(String(200))
    payment_method = Column(String(100))


class ProformaFinancingMonthly(Base):
    __tablename__ = "proforma_financing_monthly"
    id = Column(Integer, primary_key=True, autoincrement=True)
    period = Column(String(10), nullable=False)
    loan = Column(String(100), nullable=False)
    flow_type = Column(String(50), nullable=False)
    value = Column(Float, nullable=False)
    __table_args__ = (UniqueConstraint("period", "loan", "flow_type"),)


class ProformaLoans(Base):
    __tablename__ = "proforma_loans"
    id = Column(Integer, primary_key=True, autoincrement=True)
    loan_name = Column(String(100), nullable=False)
    display_name = Column(String(200))
    principal = Column(Float)
    rate = Column(Float)
    origination_year = Column(Integer)
    origination_month = Column(Integer)
    total_owed = Column(Float)
    style = Column(String(100))


class ProformaMetadata(Base):
    __tablename__ = "proforma_metadata"
    id = Column(Integer, primary_key=True, autoincrement=True)
    tab_name = Column(String(200), nullable=False)
    description = Column(Text)
    row_count = Column(Integer)
    col_count = Column(Integer)
    data_start_period = Column(String(10))
    data_end_period = Column(String(10))
    key_metrics = Column(Text)
    notes = Column(Text)
    last_updated = Column(String(50))


class ProformaTempWorkers(Base):
    __tablename__ = "proforma_temp_workers"
    id = Column(Integer, primary_key=True, autoincrement=True)
    period = Column(String(10), nullable=False)
    department = Column(String(100), nullable=False)
    value = Column(Float, nullable=False)
    __table_args__ = (UniqueConstraint("period", "department"),)


# ============================================================
# AD / MARKETING TABLES
# ============================================================

class AdDailyPlatform(Base):
    __tablename__ = "ad_daily_platform"
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(String(10), nullable=False)
    metric = Column(String(50), nullable=False)
    value = Column(Float, nullable=False)
    __table_args__ = (
        UniqueConstraint("date", "metric"),
        Index("idx_ad_daily_date", "date"),
    )


class AdMonthlyPerformance(Base):
    __tablename__ = "ad_monthly_performance"
    id = Column(Integer, primary_key=True, autoincrement=True)
    year = Column(Integer, nullable=False)
    month = Column(String(20), nullable=False)
    period = Column(String(10), nullable=False)
    total_ad_spend = Column(Float)
    com_sales = Column(Float)
    amz_sales = Column(Float)
    tiktok_sales = Column(Float)
    etsy_sales = Column(Float)
    seph_sales = Column(Float)
    total_sales = Column(Float)
    roas = Column(Float)
    new_customers = Column(Integer)
    cac = Column(Float)
    fb_spend = Column(Float)
    ggl_spend = Column(Float)
    amz_ads = Column(Float)
    seph_ads = Column(Float)
    pin_spend = Column(Float)
    snap_spend = Column(Float)
    ttk_spend = Column(Float)
    other_spend = Column(Float)
    __table_args__ = (UniqueConstraint("year", "month"),)


class FacebookAdsDaily(Base):
    __tablename__ = "facebook_ads_daily"
    date = Column(Date, primary_key=True, nullable=False)
    account_id = Column(String(50), primary_key=True, nullable=False)
    campaign_id = Column(String(50), primary_key=True)
    adset_id = Column(String(50), primary_key=True)
    ad_id = Column(String(50), primary_key=True)
    account_name = Column(String(200))
    campaign = Column(String(500))
    adset_name = Column(String(500))
    ad_name = Column(String(500))
    spend = Column(Float)
    impressions = Column(Integer)
    clicks = Column(Integer)
    reach = Column(Integer)
    cpc = Column(Float)
    cpm = Column(Float)
    ctr = Column(Float)
    frequency = Column(Float)
    purchases = Column(Integer)
    purchase_value = Column(Float)
    add_to_carts = Column(Integer)
    checkouts_initiated = Column(Integer)
    link_clicks = Column(Integer)
    landing_page_views = Column(Integer)
    video_views = Column(Integer)
    roas = Column(Float)
    synced_at = Column(DateTime)


# ============================================================
# RETAIL TABLES
# ============================================================

class RetailMonthly(Base):
    __tablename__ = "retail_monthly"
    id = Column(Integer, primary_key=True, autoincrement=True)
    period = Column(String(10), nullable=False)
    retailer = Column(String(100), nullable=False)
    metric = Column(String(50), nullable=False)
    value = Column(Float, nullable=False)
    __table_args__ = (
        UniqueConstraint("period", "retailer", "metric"),
        Index("idx_retail_period", "period"),
    )


class RetailYoyMonthly(Base):
    __tablename__ = "retail_yoy_monthly"
    id = Column(Integer, primary_key=True, autoincrement=True)
    month = Column(String(10), nullable=False)
    year = Column(Integer, nullable=False)
    revenue = Column(Float, nullable=False)
    __table_args__ = (UniqueConstraint("month", "year"),)


# ============================================================
# QUICKBOOKS TABLES
# ============================================================

class QuickbooksPlMonthly(Base):
    __tablename__ = "quickbooks_pl_monthly"
    period_start = Column(Date, primary_key=True, nullable=False)
    period_end = Column(Date, nullable=False)
    total_income = Column(Float)
    total_cogs = Column(Float)
    gross_profit = Column(Float)
    total_expenses = Column(Float)
    net_income = Column(Float)
    gross_margin = Column(Float)
    net_margin = Column(Float)
    shopify_income = Column(Float)
    amazon_income = Column(Float)
    wholesale_income = Column(Float)
    other_income = Column(Float)
    product_cogs = Column(Float)
    shipping_fulfillment = Column(Float)
    merchant_fees = Column(Float)
    advertising = Column(Float)
    payroll = Column(Float)
    contractors = Column(Float)
    ga_expenses = Column(Float)
    interest_financing = Column(Float)
    depreciation = Column(Float)
    rent = Column(Float)
    software = Column(Float)
    synced_at = Column(DateTime, default=func.now())


class QuickbooksCashflowMonthly(Base):
    __tablename__ = "quickbooks_cashflow_monthly"
    period_start = Column(Date, primary_key=True, nullable=False)
    period_end = Column(Date, nullable=False)
    operating_activities = Column(Float)
    investing_activities = Column(Float)
    financing_activities = Column(Float)
    net_cash_change = Column(Float)
    cash_beginning = Column(Float)
    cash_end = Column(Float)
    net_income = Column(Float)
    synced_at = Column(DateTime, default=func.now())


# ============================================================
# SHOPIFY TABLES
# ============================================================

class ShopifyOrdersDaily(Base):
    __tablename__ = "shopify_orders_daily"
    date = Column(Date, primary_key=True, nullable=False)
    order_count = Column(Integer)
    gross_sales = Column(Float)
    discounts = Column(Float)
    refunds = Column(Float)
    net_sales = Column(Float)
    shipping_revenue = Column(Float)
    tax_collected = Column(Float)
    total_price = Column(Float)
    avg_order_value = Column(Float)
    units_sold = Column(Integer)
    new_customers = Column(Integer)
    returning_customers = Column(Integer)
    synced_at = Column(DateTime)


# ============================================================
# OPERATIONAL TABLES
# ============================================================

class CashRunway(Base):
    __tablename__ = "cash_runway"
    date = Column(String(10), primary_key=True)
    cash_balance = Column(Float)
    monthly_burn_rate = Column(Float)
    runway_months = Column(Float)
    projected_zero_date = Column(String(10))


class SyncLog(Base):
    __tablename__ = "sync_log"
    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String(100), nullable=False)
    sync_start = Column(DateTime, nullable=False)
    sync_end = Column(DateTime)
    status = Column(String(20))
    records_pulled = Column(Integer)
    error_message = Column(Text)
    date_range_from = Column(Date)
    date_range_to = Column(Date)


# ============================================================
# API KEY TABLE (for bot authentication)
# ============================================================

class ApiKey(Base):
    __tablename__ = "api_keys"
    id = Column(Integer, primary_key=True, autoincrement=True)
    key_hash = Column(String(128), nullable=False, unique=True)
    name = Column(String(100), nullable=False)
    role = Column(String(20), nullable=False, default="read")  # read, write, admin
    created_at = Column(DateTime, default=func.now())
    last_used = Column(DateTime)
    is_active = Column(Boolean, default=True)


def get_engine():
    db_url = os.environ.get("DATABASE_URL", "")
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    return create_engine(db_url)


def get_session():
    engine = get_engine()
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    return Session()
