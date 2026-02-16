"""
积分系统模块 - 记录和计算默契值
"""
from datetime import datetime, timedelta

import streamlit as st

from database import PointsLog, get_session


def add_points(user, points, description):
    """添加积分记录。"""
    session = get_session()
    try:
        log = PointsLog(
            user=user,
            action="app_action",
            points=points,
            description=description,
            created_at=datetime.now(),
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
    """获取用户最近积分。"""
    session = get_session()
    try:
        cutoff = datetime.now() - timedelta(days=days)
        logs = (
            session.query(PointsLog)
            .filter(PointsLog.user == user, PointsLog.created_at >= cutoff)
            .order_by(PointsLog.created_at.desc())
            .all()
        )

        total = sum(log.points for log in logs)
        return total, logs
    finally:
        session.close()


def get_points_ranking():
    """获取两人积分对比。"""
    me_total, me_logs = get_user_points("me")
    him_total, him_logs = get_user_points("him")

    return {
        "me": {"total": me_total, "logs": me_logs},
        "him": {"total": him_total, "logs": him_logs},
    }


def get_achievement_level(points):
    """根据积分获取称号。"""
    if points >= 1000:
        return "🏆 冠军情侣"
    if points >= 500:
        return "🥇 金牌搭档"
    if points >= 300:
        return "🥈 银牌搭档"
    if points >= 100:
        return "🥉 铜牌搭档"
    return "🏸 新晋球友"


def render_points():
    """渲染积分页面。"""
    st.markdown("## 🎁 积分奖赏")
    ranking = get_points_ranking()

    col1, col2 = st.columns(2)
    with col1:
        st.metric("💕 我", ranking["me"]["total"])
        st.caption(get_achievement_level(ranking["me"]["total"]))
    with col2:
        st.metric("🏸 他", ranking["him"]["total"])
        st.caption(get_achievement_level(ranking["him"]["total"]))

    current_user = st.session_state.get("user", "me")
    _, logs = get_user_points(current_user, days=30)
    st.markdown("### 最近30天积分记录")
    if logs:
        st.dataframe(
            [
                {
                    "时间": log.created_at.strftime("%Y-%m-%d %H:%M"),
                    "积分": log.points,
                    "说明": log.description,
                }
                for log in logs
            ],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("最近30天还没有积分记录。")
