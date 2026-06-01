"""
维护提醒系统的配置。
所有敏感数据应从环境变量中加载。
"""

import os
from dotenv import load_dotenv

# 从 .env 文件加载环境变量（用于本地测试）
load_dotenv()

# Google 表格配置
GOOGLE_SHEET_NAME = os.getenv('GOOGLE_SHEET_NAME', 'Maintenance Schedule')
GOOGLE_CREDENTIALS_JSON = os.getenv('GOOGLE_CREDENTIALS_JSON', 'credentials/google_credentials.json')

# SendGrid 配置
SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY')
SENDER_EMAIL = os.getenv('SENDER_EMAIL', 'titatn818@gmail.com')
SENDER_NAME = os.getenv('SENDER_NAME', 'Maintenance System')

# Email Configuration
REMINDER_DAYS_BEFORE = 7  # Send reminder 7 days before maintenance due
TIMEZONE = 'Asia/Jakarta'  # Adjust to your timezone

# Column names in Google Sheet (adjust based on your sheet structure)
COLUMNS = {
    'asset_id': 'Asset ID',
    'asset_name': 'Asset Name',
    'maintenance_date': 'Maintenance Date',
    'pic_email': 'PIC Email',
    'pic_name': 'PIC Name',
    'status': 'Status'
}