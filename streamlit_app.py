"""
CrushCourt - 你们的专属爱情球场 🏸❤️
双人互动恋爱App，让日常记录变成一场有趣的羽毛球游戏
"""
import streamlit as st
from pathlib import Path

from database import init_database
from court import render_court
from points import render_points


# 页面配置 - 必须放在最前面
st.set_page_config(
    page_title="CrushCourt",
    page_icon="🏸",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def load_css() -> None:
    """加载自定义CSS。"""
    css_path = Path(__file__).with_name("style.css")
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


def render_health() -> None:
    """健康模块占位。"""
    st.header("💧 健康管理")
    st.info("该模块正在建设中，可先使用双人球场与积分功能。")


def render_tasks() -> None:
    """赛事任务模块占位。"""
    st.header("🏆 赛事任务")
    st.info("该模块正在建设中，可先使用双人球场与积分功能。")


def render_honors() -> None:
    """荣誉模块占位。"""
    st.header("🏅 荣誉殿堂")
    st.info("该模块正在建设中，可先使用双人球场与积分功能。")


# 初始化数据库
init_database()

if "user" not in st.session_state:
    st.session_state.user = None


def login() -> None:
    """简单的双人登录界面。"""
    st.markdown(
        """
    <div style='text-align: center; padding: 50px;'>
        <h1 style='color: white; font-size: 48px;'>🏸 CrushCourt</h1>
        <p style='color: rgba(255,255,255,0.8); font-size: 20px;'>欢迎来到你们的专属爱情球场</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    _, col2, _ = st.columns([1, 1, 1])
    with col2:
        st.markdown('<div class="court-card">', unsafe_allow_html=True)
        st.markdown("### 选择你的身份")
        if st.button("💕 我", use_container_width=True):
            st.session_state.user = "me"
            st.rerun()
        if st.button("🏸 他", use_container_width=True):
            st.session_state.user = "him"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)


def main() -> None:
    """应用主界面。"""
    with st.sidebar:
        st.markdown(
            f"""
        <div style='text-align: center; padding: 20px;'>
            <div class='shuttlecock'>🏸</div>
            <h3>{'💕 我' if st.session_state.user == 'me' else '🏸 他'}</h3>
        </div>
        """,
            unsafe_allow_html=True,
        )

        menu = st.radio(
            "导航",
            ["🏸 双人球场", "💧 健康管理", "🏆 赛事任务", "🏅 荣誉殿堂", "🎁 积分奖赏"],
            label_visibility="collapsed",
        )

        if st.button("🚪 退出登录", use_container_width=True):
            st.session_state.user = None
            st.rerun()

    if menu == "🏸 双人球场":
        render_court()
    elif menu == "💧 健康管理":
        render_health()
    elif menu == "🏆 赛事任务":
        render_tasks()
    elif menu == "🏅 荣誉殿堂":
        render_honors()
    elif menu == "🎁 积分奖赏":
        render_points()


load_css()
if st.session_state.user is None:
    login()
else:
    main()
