"""
积分系统模块 - 记录和计算默契值
"""
import streamlit as st
from modules import get_session, PointsLog
from datetime import datetime, timedelta

def add_points(user, points, description):
    """添加积分记录"""
    session = get_session()
    try:
        log = PointsLog(
            user=user,
            points=points,
            description=description,
            created_at=datetime.now()
        )
        session.add(log)
        session.commit()
        return True
    except Exception as e:
        print(f"积分添加失败：{e}")
        session.rollback()
        return False
    finally:
        session.close()

def get_user_points(user, days=30):
    """获取用户最近积分"""
    session = get_session()
    try:
        cutoff = datetime.now() - timedelta(days=days)
        logs = session.query(PointsLog).filter(
            PointsLog.user == user,
            PointsLog.created_at >= cutoff
        ).all()
        
        total = sum(log.points for log in logs)
        return total, logs
    finally:
        session.close()

def get_points_ranking():
    """获取两人积分对比"""
    me_total, me_logs = get_user_points('me')
    him_total, him_logs = get_user_points('him')
    
    return {
        'me': {'total': me_total, 'logs': me_logs},
        'him': {'total': him_total, 'logs': him_logs}
    }

def get_achievement_level(points):
    """根据积分获取称号"""
    if points >= 1000:
        return "🏆 冠军情侣"
    elif points >= 500:
        return "🥇 金牌搭档"
    elif points >= 300:
        return "🥈 银牌搭档"
    elif points >= 100:
        return "🥉 铜牌搭档"
    else:
        return "🏸 新晋球友"