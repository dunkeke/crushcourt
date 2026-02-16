"""赛事任务模块。"""
from datetime import datetime, timedelta

import streamlit as st

from database import MatchReminder, get_session
from points import add_points


def create_match_task(title: str, opponent: str, match_date: datetime, location: str, created_by: str) -> bool:
    session = get_session()
    try:
        reminder = MatchReminder(
            title=title,
            opponent=opponent,
            match_date=match_date,
            location=location,
            reminder_time=match_date - timedelta(hours=2),
            is_completed=False,
            created_by=created_by,
            created_at=datetime.now(),
        )
        session.add(reminder)
        session.commit()
        return True
    except Exception as e:
        st.error(f"创建任务失败：{e}")
        session.rollback()
        return False
    finally:
        session.close()


def get_match_tasks(show_completed: bool = False):
    session = get_session()
    try:
        query = session.query(MatchReminder)
        if not show_completed:
            query = query.filter(MatchReminder.is_completed.is_(False))
        return query.order_by(MatchReminder.match_date.asc()).all()
    finally:
        session.close()


def complete_match_task(task_id: int, user: str) -> bool:
    session = get_session()
    try:
        task = session.query(MatchReminder).filter(MatchReminder.id == task_id).first()
        if not task:
            return False
        task.is_completed = True
        session.commit()
        add_points(user, 8, f"完成赛事任务：{task.title}")
        return True
    except Exception as e:
        st.error(f"更新任务失败：{e}")
        session.rollback()
        return False
    finally:
        session.close()


def render_tasks() -> None:
    st.markdown("## 🏆 赛事任务")
    st.caption("把比赛安排公开透明，互相支持。")

    left, right = st.columns([1, 1])

    with left:
        st.markdown("### 新建赛事")
        with st.form("match_task_form"):
            title = st.text_input("赛事名称", placeholder="周末混双训练赛")
            opponent = st.text_input("对手/搭档")
            match_day = st.date_input("比赛日期", value=datetime.now().date())
            match_time = st.time_input("比赛时间", value=(datetime.now() + timedelta(hours=2)).time())
            location = st.text_input("地点", placeholder="市体育馆")
            submitted = st.form_submit_button("➕ 添加赛事", use_container_width=True)
            if submitted and title:
                match_dt = datetime.combine(match_day, match_time)
                if create_match_task(title, opponent, match_dt, location, st.session_state.user):
                    st.success("赛事任务已添加")
                    st.rerun()

    with right:
        st.markdown("### 待完成赛事")
        tasks = get_match_tasks(show_completed=False)
        if tasks:
            for task in tasks:
                with st.container(border=True):
                    st.write(f"**{task.title}**")
                    st.caption(
                        f"{task.match_date.strftime('%Y-%m-%d %H:%M')} · "
                        f"地点：{task.location or '待定'} · 对手：{task.opponent or '待定'}"
                    )
                    created_by = "💕 我" if task.created_by == "me" else "🏸 他"
                    st.caption(f"创建人：{created_by} · 提醒：{task.reminder_time.strftime('%m-%d %H:%M')}")
                    if st.button("✅ 已完成", key=f"task_done_{task.id}", use_container_width=True):
                        if complete_match_task(task.id, st.session_state.user):
                            st.success("已标记完成 +8 积分")
                            st.rerun()
        else:
            st.info("暂无待完成赛事。")

    with st.expander("查看已完成赛事"):
        done_tasks = get_match_tasks(show_completed=True)
        done_tasks = [x for x in done_tasks if x.is_completed]
        if done_tasks:
            st.dataframe(
                [
                    {
                        "赛事": x.title,
                        "时间": x.match_date.strftime("%Y-%m-%d %H:%M"),
                        "地点": x.location or "待定",
                    }
                    for x in done_tasks
                ],
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.caption("暂无完成记录")
