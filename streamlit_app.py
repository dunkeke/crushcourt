"""
CrushCourt - 你们的专属爱情球场 🏸❤️
双人互动恋爱App，让日常记录变成一场有趣的羽毛球游戏
"""
import streamlit as st
import pandas as pd
from datetime import datetime
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# 导入自定义模块
from modules import get_session, LoveRecord, init_database
from modules.court import render_court
from modules.health import render_health
from modules.tasks import render_tasks
from modules.honors import render_honors
from modules.points import render_points

# 页面配置 - 必须放在最前面
st.set_page_config(
    page_title="CrushCourt",
    page_icon="🏸",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 加载自定义CSS
def load_css():
    with open('assets/style.css') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# 初始化数据库
init_database()

# 设置用户身份（固定两人使用）
if 'user' not in st.session_state:
    st.session_state.user = None

def login():
    """简单的双人登录界面"""
    st.markdown("""
    <div style='text-align: center; padding: 50px;'>
        <h1 style='color: white; font-size: 48px;'>🏸 CrushCourt</h1>
        <p style='color: rgba(255,255,255,0.8); font-size: 20px;'>欢迎来到你们的专属爱情球场</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.markdown('<div class="court-card">', unsafe_allow_html=True)
        st.markdown("### 选择你的身份")
        if st.button("💕 我", use_container_width=True):
            st.session_state.user = 'me'
            st.rerun()
        if st.button("🏸 他", use_container_width=True):
            st.session_state.user = 'him'
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# 主界面
def main():
    # 侧边栏
    with st.sidebar:
        st.markdown(f"""
        <div style='text-align: center; padding: 20px;'>
            <div class='shuttlecock'>🏸</div>
            <h3>{'💕 我' if st.session_state.user == 'me' else '🏸 他'}</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # 导航菜单
        menu = st.radio(
            "导航",
            ["🏸 双人球场", "💧 健康管理", "🏆 赛事任务", "🏅 荣誉殿堂", "🎁 积分奖赏"],
            label_visibility="collapsed"
        )
        
        if st.button("🚪 退出登录", use_container_width=True):
            st.session_state.user = None
            st.rerun()
    
    # 主要内容区
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

# 运行应用
if __name__ == "__main__":
    load_css()
    if st.session_state.user is None:
        login()
    else:
        main()