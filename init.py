# 模块初始化文件
from .database import init_database, get_session
from .database import (
    LoveRecord, HealthReminder, HealthLog, 
    MatchReminder, HonorRecord, PointsLog
)

# 初始化数据库
init_database()