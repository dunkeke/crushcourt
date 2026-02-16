"""
数据库模块 - 存储所有的爱情记录
"""
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

# 数据库文件路径
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'crush_court.db')
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

# 创建数据库引擎
engine = create_engine(f'sqlite:///{DB_PATH}', echo=False)
Base = declarative_base()
Session = sessionmaker(bind=engine)

class LoveRecord(Base):
    """双人回球记录 - 核心功能"""
    __tablename__ = 'love_records'
    
    id = Column(Integer, primary_key=True)
    sender = Column(String)  # 'me' 或 'him'
    receiver = Column(String)  # 接收方
    record_type = Column(String)  # 'work', 'life', 'love'
    action = Column(String)  # 'serve'发球, 'return'回球, 'smash'扣杀, 'drop'放网
    content = Column(Text)  # 记录内容
    emotion_score = Column(Float, default=5.0)  # 情绪分数 1-10
    is_read = Column(Boolean, default=False)  # 是否被对方查看
    is_responded = Column(Boolean, default=False)  # 是否被回应
    created_at = Column(DateTime, default=datetime.utcnow)
    responded_at = Column(DateTime, nullable=True)

class HealthReminder(Base):
    """健康提醒 - 喝水吃饭提醒"""
    __tablename__ = 'health_reminders'
    
    id = Column(Integer, primary_key=True)
    reminder_type = Column(String)  # 'water', 'breakfast', 'lunch', 'dinner', 'sleep'
    reminder_time = Column(String)  # 格式 "HH:MM"
    message = Column(String)  # 自定义提醒内容
    set_by = Column(String)  # 'me' 或 'him'
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class HealthLog(Base):
    """健康记录 - 实际完成情况"""
    __tablename__ = 'health_logs'
    
    id = Column(Integer, primary_key=True)
    reminder_id = Column(Integer)  # 关联的提醒
    user = Column(String)  # 'me' 或 'him'
    completed_at = Column(DateTime, default=datetime.utcnow)
    note = Column(String, nullable=True)

class MatchReminder(Base):
    """赛事任务 - 男友比赛提醒"""
    __tablename__ = 'match_reminders'
    
    id = Column(Integer, primary_key=True)
    title = Column(String)  # 比赛名称
    opponent = Column(String)  # 对手
    match_date = Column(DateTime)
    location = Column(String)
    reminder_time = Column(DateTime)  # 提前提醒时间
    is_completed = Column(Boolean, default=False)
    created_by = Column(String)  # 一般是'him'
    created_at = Column(DateTime, default=datetime.utcnow)

class HonorRecord(Base):
    """荣誉殿堂 - 美好时刻记录"""
    __tablename__ = 'honor_records'
    
    id = Column(Integer, primary_key=True)
    title = Column(String)  # 标题，比如"第一次一起看比赛"
    description = Column(Text)
    honor_type = Column(String)  # 'milestone'纪念日, 'achievement'成就, 'memory'回忆
    photo_url = Column(String, nullable=True)  # 可以存图片路径或base64
    emotion_score = Column(Float)  # 当时的开心程度
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String)

class PointsLog(Base):
    """积分系统 - 奖赏机制"""
    __tablename__ = 'points_log'
    
    id = Column(Integer, primary_key=True)
    user = Column(String)  # 'me' 或 'him'
    action = Column(String)  # 'reply_record', 'remind_water', 'attend_match'等
    points = Column(Integer)
    description = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

# 创建所有表
def init_database():
    """初始化数据库，创建表"""
    Base.metadata.create_all(engine)
    print(f"✅ 数据库初始化成功：{DB_PATH}")

def get_session():
    """获取数据库会话"""
    return Session()