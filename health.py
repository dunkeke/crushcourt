"""健康管理模块。"""
from datetime import datetime

import streamlit as st

from database import HealthLog, HealthReminder, get_session
from points import add_points


REMINDER_TYPES = {
    "water": "💧 喝水",
    "breakfast": "🍳 早餐",
    "lunch": "🍱 午餐",
    "dinner": "🍲 晚餐",
    "sleep": "🌙 睡眠",
}


def create_reminder(reminder_type: str, reminder_time: str, message: str, set_by: str) -> bool:
    session = get_session()
    try:
        reminder = HealthReminder(
            reminder_type=reminder_type,
            reminder_time=reminder_time,
            message=message,
            set_by=set_by,
            is_active=True,
            created_at=datetime.now(),
        )
        session.add(reminder)
        session.commit()
        return True
    except Exception as e:
        st.error(f"创建提醒失败：{e}")
        session.rollback()
        return False
    finally:
        session.close()


def get_active_reminders():
    session = get_session()
    try:
        return (
            session.query(HealthReminder)
            .filter(HealthReminder.is_active.is_(True))
            .order_by(HealthReminder.reminder_time.asc())
            .all()
        )
    finally:
        session.close()


def complete_reminder(reminder_id: int, user: str, note: str = "") -> bool:
    session = get_session()
    try:
        log = HealthLog(
            reminder_id=reminder_id,
            user=user,
            completed_at=datetime.now(),
            note=note or None,
        )
        session.add(log)
        session.commit()
        add_points(user, 2, "完成健康打卡")
        return True
    except Exception as e:
        st.error(f"打卡失败：{e}")
        session.rollback()
        return False
    finally:
        session.close()


def get_recent_health_logs(limit: int = 20):
    session = get_session()
    try:
        return session.query(HealthLog).order_by(HealthLog.completed_at.desc()).limit(limit).all()
    finally:
        session.close()


def render_health() -> None:
    st.markdown("## 💧 健康管理")
    st.caption("互相提醒 + 打卡记录，形成日常照顾节奏。")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("### 新建提醒")
        with st.form("health_reminder_form"):
            reminder_type = st.selectbox(
                "提醒类型",
                options=list(REMINDER_TYPES.keys()),
                format_func=lambda x: REMINDER_TYPES[x],
            )
            reminder_time = st.time_input("提醒时间", value=datetime.now().time())
            message = st.text_input("提醒内容", placeholder="记得喝一杯温水～")
            submitted = st.form_submit_button("➕ 添加提醒", use_container_width=True)
            if submitted:
                if create_reminder(
                    reminder_type,
                    reminder_time.strftime("%H:%M"),
                    message or f"{REMINDER_TYPES[reminder_type]}时间到啦",
                    st.session_state.user,
                ):
                    st.success("提醒已创建")
                    st.rerun()

    with col2:
        st.markdown("### 活跃提醒")
        reminders = get_active_reminders()
        if reminders:
            for reminder in reminders:
                with st.container(border=True):
                    st.write(
                        f"{REMINDER_TYPES.get(reminder.reminder_type, '⏰ 提醒')} "
                        f"**{reminder.reminder_time}** · 来自 {'💕 我' if reminder.set_by == 'me' else '🏸 他'}"
                    )
                    st.caption(reminder.message)
                    note = st.text_input("打卡备注", key=f"note_{reminder.id}")
                    if st.button("✅ 我已完成", key=f"done_{reminder.id}", use_container_width=True):
                        if complete_reminder(reminder.id, st.session_state.user, note):
                            st.success("打卡成功 +2 积分")
                            st.rerun()
        else:
            st.info("还没有提醒，先创建一条吧。")

    st.markdown("### 最近健康打卡")
    logs = get_recent_health_logs()
    if logs:
        st.dataframe(
            [
                {
                    "时间": x.completed_at.strftime("%Y-%m-%d %H:%M"),
                    "用户": "💕 我" if x.user == "me" else "🏸 他",
                    "备注": x.note or "-",
                }
                for x in logs
            ],
            hide_index=True,
            use_container_width=True,
        )
    else:
        st.info("暂无打卡记录。")
