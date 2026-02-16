"""
双人球场模块 - 用羽毛球回球的方式记录生活
发球：分享心情/事件
回球：回应对方
扣杀：强调重要事项
放网：温柔回应
"""
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from database import get_session, LoveRecord
from visualizations import create_emotion_timeline
import plotly.graph_objects as go

# 记录类型和对应的emoji
RECORD_TYPES = {
    'work': '💼 工作',
    'life': '🏠 生活', 
    'love': '💕 爱情'
}

# 动作类型和对应的描述
ACTIONS = {
    'serve': {
        'name': '发球',
        'emoji': '🏐',
        'color': '#4CAF50',
        'desc': '分享新鲜事'
    },
    'return': {
        'name': '回球',
        'emoji': '⚡',
        'color': '#2196F3',
        'desc': '回应对方'
    },
    'smash': {
        'name': '扣杀',
        'emoji': '💥',
        'color': '#f44336',
        'desc': '重要提醒'
    },
    'drop': {
        'name': '放网',
        'emoji': '🕸️',
        'color': '#FF9800',
        'desc': '温柔回应'
    }
}

def get_user_display(user):
    """获取用户显示名称"""
    return '💕 我' if user == 'me' else '🏸 他'

def save_love_record(sender, receiver, record_type, action, content, emotion_score=5.0):
    """保存一条爱情记录"""
    session = get_session()
    try:
        record = LoveRecord(
            sender=sender,
            receiver=receiver,
            record_type=record_type,
            action=action,
            content=content,
            emotion_score=emotion_score,
            created_at=datetime.now()
        )
        session.add(record)
        session.commit()
        
        # 如果是发球，给对方加积分
        if action == 'serve':
            from points import add_points
            add_points(sender, 5, f'发布新动态：{content[:20]}...')
        
        return True
    except Exception as e:
        st.error(f"保存失败：{e}")
        session.rollback()
        return False
    finally:
        session.close()

def get_recent_records(days=3, limit=50):
    """获取最近几天的记录"""
    session = get_session()
    try:
        cutoff = datetime.now() - timedelta(days=days)
        records = session.query(LoveRecord).filter(
            LoveRecord.created_at >= cutoff
        ).order_by(
            LoveRecord.created_at.desc()
        ).limit(limit).all()
        return records
    finally:
        session.close()

def get_pending_records(user):
    """获取待回应的记录（发给该用户但未读或未回应的）"""
    session = get_session()
    try:
        # 发给该用户且未回应或未读
        records = session.query(LoveRecord).filter(
            LoveRecord.receiver == user,
            LoveRecord.is_responded == False
        ).order_by(
            LoveRecord.created_at.desc()
        ).all()
        return records
    finally:
        session.close()

def respond_to_record(record_id, response_action, response_content):
    """回应一条记录"""
    session = get_session()
    try:
        # 更新原记录
        record = session.query(LoveRecord).filter(LoveRecord.id == record_id).first()
        if record:
            record.is_read = True
            record.is_responded = True
            record.responded_at = datetime.now()
            
            # 创建回应记录
            response = LoveRecord(
                sender=st.session_state.user,
                receiver=record.sender,
                record_type=record.record_type,
                action=response_action,
                content=response_content,
                emotion_score=record.emotion_score,  # 可以继承情绪分数
                created_at=datetime.now(),
                is_read=False
            )
            session.add(response)
            session.commit()
            
            # 加分：回应对方
            from points import add_points
            add_points(st.session_state.user, 3, f'回应了{get_user_display(record.sender)}')
            
            return True
    except Exception as e:
        st.error(f"回应失败：{e}")
        session.rollback()
        return False
    finally:
        session.close()

def render_court():
    """渲染双人球场主界面"""
    st.markdown("""
    <div style='text-align: center; padding: 20px;'>
        <h1 style='color: white;'>🏸 双人球场</h1>
        <p style='color: rgba(255,255,255,0.8);'>用回球记录彼此的每一天</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 创建三列：我、球网、他
    col1, net_col, col2 = st.columns([5, 1, 5])
    
    # ========== 左侧：我的场地 ==========
    with col1:
        st.markdown(f"""
        <div class='court-card'>
            <h3>{'💕 我的场地' if st.session_state.user == 'me' else '🏸 他的场地'}</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # 发球区（分享今日）
        with st.expander("🎯 发球 - 分享今日", expanded=True):
            with st.form("serve_form"):
                # 记录类型选择
                record_type = st.selectbox(
                    "选择类型",
                    options=list(RECORD_TYPES.keys()),
                    format_func=lambda x: RECORD_TYPES[x]
                )
                
                # 内容输入
                content = st.text_area("记录内容", placeholder="今天发生了什么有趣的事？")
                
                # 情绪评分
                emotion = st.slider("今日心情", 1, 10, 5, 
                                   help="1=阴天 ☁️ → 10=晴天 ☀️")
                
                # 动作选择（发球时可选）
                action = st.radio(
                    "发球方式",
                    options=['serve', 'smash', 'drop'],
                    format_func=lambda x: f"{ACTIONS[x]['emoji']} {ACTIONS[x]['name']} - {ACTIONS[x]['desc']}",
                    horizontal=True
                )
                
                submitted = st.form_submit_button("🏐 发球", use_container_width=True)
                if submitted and content:
                    receiver = 'him' if st.session_state.user == 'me' else 'me'
                    if save_love_record(st.session_state.user, receiver, record_type, action, content, emotion):
                        st.success("✅ 发球成功！等待对方回球...")
                        st.rerun()
    
    # ========== 中间：球网 ==========
    with net_col:
        st.markdown("""
        <div style='height: 100%; display: flex; flex-direction: column; justify-content: center;'>
            <div class='court-net'></div>
            <div style='text-align: center; margin-top: 20px;'>
                <span class='shuttlecock'>🏸</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # ========== 右侧：对方场地 & 待回应区 ==========
    with col2:
        st.markdown(f"""
        <div class='court-card'>
            <h3>{'🏸 他的场地' if st.session_state.user == 'me' else '💕 我的场地'}</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # 获取待回应的记录
        other_user = 'him' if st.session_state.user == 'me' else 'me'
        pending_records = get_pending_records(st.session_state.user)
        
        if pending_records:
            st.markdown("### 🎯 待回应的球")
            for record in pending_records:
                with st.container():
                    # 根据动作类型显示不同样式
                    action_info = ACTIONS.get(record.action, ACTIONS['serve'])
                    
                    # 创建卡片式显示
                    st.markdown(f"""
                    <div style='
                        background: {action_info["color"]}10;
                        border-left: 4px solid {action_info["color"]};
                        padding: 10px;
                        margin: 10px 0;
                        border-radius: 5px;
                    '>
                        <div style='display: flex; justify-content: space-between;'>
                            <span>{action_info["emoji"]} {get_user_display(record.sender)} 发来一球</span>
                            <span style='color: gray;'>{record.created_at.strftime("%H:%M")}</span>
                        </div>
                        <div style='font-size: 1.1em; margin: 5px 0;'>{record.content}</div>
                        <div style='display: flex; gap: 5px;'>
                            <span>类型：{RECORD_TYPES[record.record_type]}</span>
                            <span>心情：{'☀️' * int(record.emotion_score)}{'☁️' * (10 - int(record.emotion_score))}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # 回应按钮
                    with st.expander("⚡ 回球"):
                        # 获取当前时间作为唯一键
                        timestamp = datetime.now().timestamp()
                        
                        response_content = st.text_area(
                            "你的回应",
                            key=f"response_{record.id}_{timestamp}",
                            placeholder="写下你的回应..."
                        )
                        
                        response_action = st.radio(
                            "回应方式",
                            options=['return', 'smash', 'drop'],
                            format_func=lambda x: f"{ACTIONS[x]['emoji']} {ACTIONS[x]['name']}",
                            horizontal=True,
                            key=f"action_{record.id}_{timestamp}"
                        )
                        
                        if st.button(f"⚡ 回球给{get_user_display(record.sender)}", 
                                   key=f"btn_{record.id}_{timestamp}",
                                   use_container_width=True):
                            if response_content:
                                if respond_to_record(record.id, response_action, response_content):
                                    st.success("✅ 回球成功！")
                                    st.rerun()
                            else:
                                st.warning("请输入回应内容")
        else:
            st.info("🏸 暂无待回应的球，去发个球吧！")
    
    # ========== 底部：最近记录时间线 ==========
    st.markdown("---")
    st.markdown("### 📊 最近3天的球路轨迹")
    
    records = get_recent_records(days=3)
    if records:
        # 转换为DataFrame用于可视化
        data = []
        for r in records:
            data.append({
                '时间': r.created_at,
                '发送者': get_user_display(r.sender),
                '类型': RECORD_TYPES[r.record_type],
                '动作': ACTIONS[r.action]['emoji'],
                '内容': r.content[:20] + '...' if len(r.content) > 20 else r.content,
                '心情': r.emotion_score
            })
        
        df = pd.DataFrame(data)
        
        # 使用Plotly创建时间线
        fig = create_emotion_timeline(records)
        st.plotly_chart(fig, use_container_width=True)
        
        # 显示最近记录表格
        with st.expander("📋 查看详细记录"):
            st.dataframe(
                df[['时间', '发送者', '类型', '动作', '内容', '心情']],
                use_container_width=True,
                hide_index=True
            )
    else:
        st.info("还没有记录，去发第一个球吧！")