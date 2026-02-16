"""
CrushCourt - 你们的专属爱情球场 🏸❤️
双人互动恋爱App，让日常记录变成一场有趣的羽毛球游戏
"""
import os
from pathlib import Path

import streamlit as st

from court import render_court
from database import init_database
from health import render_health
from points import render_points
from tasks import render_tasks


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


def render_honors() -> None:
    """荣誉模块占位。"""
    st.header("🏅 荣誉殿堂")
    st.info("该模块正在建设中，可先使用双人球场/健康/赛事/积分功能。")


def get_user_passwords() -> dict:
    """读取双人进入密码（优先 secrets，其次环境变量，最后开发默认值）。"""
    default_pw = {"me": "change-me-💕", "him": "change-him-🏸"}

    try:
        secret_pw = st.secrets.get("access_passwords")
        # Streamlit secrets 的子表通常是 AttrDict，不一定是原生 dict
        if secret_pw and secret_pw.get("me") and secret_pw.get("him"):
            return {"me": str(secret_pw.get("me")), "him": str(secret_pw.get("him"))}
    except Exception:
        pass

    env_me = os.getenv("CRUSHCOURT_PW_ME")
    env_him = os.getenv("CRUSHCOURT_PW_HIM")
    if env_me and env_him:
        return {"me": env_me, "him": env_him}

    return default_pw


init_database()

if "user" not in st.session_state:
    st.session_state.user = None
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False


def login() -> None:
    """双人身份+密码登录。"""
    st.markdown(
        """
    <div style='text-align: center; padding: 40px;'>
        <h1 style='color: white; font-size: 48px;'>🏸 CrushCourt</h1>
        <p style='color: rgba(255,255,255,0.88); font-size: 19px;'>你们的专属沟通球场（双人入口）</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    _, col2, _ = st.columns([1, 1, 1])
    passwords = get_user_passwords()

    with col2:
        st.markdown('<div class="court-card">', unsafe_allow_html=True)
        role = st.radio("选择身份", options=["me", "him"], format_func=lambda x: "💕 我" if x == "me" else "🏸 他")
        password = st.text_input("进入密码", type="password", placeholder="输入专属密码")

        if st.button("🔐 进入球场", use_container_width=True):
            if password == passwords.get(role):
                st.session_state.user = role
                st.session_state.authenticated = True
                st.success("进入成功")
                st.rerun()
            else:
                st.error("密码错误，请重试")

        if passwords["me"].startswith("change-"):
            st.warning("请在 Streamlit secrets 或环境变量中设置正式密码，默认密码仅用于开发。")

        st.markdown("</div>", unsafe_allow_html=True)


def main() -> None:
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
            st.session_state.authenticated = False
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
if not st.session_state.authenticated or st.session_state.user is None:
    login()
else:
    main()
