"""
赛事任务模块 - 男友比赛提醒和助威
功能：
- 添加比赛日程
- 比赛提醒
- 赛前助威/赛后庆祝
- 比赛结果记录
- 积分奖励
"""
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date
from modules import get_session, MatchReminder
import plotly.graph_objects as go
import calendar

# 比赛状态配置
MATCH_STATUS = {
    'upcoming': {
        'name': '⏳ 即将开始',
        'color': '#FFA500',
        'emoji': '⏰'
    },
    'ongoing': {
        'name': '⚡ 进行中',
        'color': '#4CAF50',
        'emoji': '🏃'
    },
    'completed': {
        'name': '✅ 已结束',
        'color': '#808080',
        'emoji': '🏁'
    },
    'cancelled': {
        'name': '❌ 已取消',
        'color': '#f44336',
        'emoji': '🚫'
    }
}

# 助威方式
CHEER_TYPES = {
    'message': {
        'name': '💬 加油 message',
        'emoji': '💬',
        'points': 5
    },
    'voice': {
        'name': '🎤 语音助威',
        'emoji': '🎤',
        'points': 8
    },
    'surprise': {
        'name': '🎁 惊喜到场',
        'emoji': '🎁',
        'points': 20
    },
    'celebration': {
        'name': '🎉 赛后庆祝',
        'emoji': '🎉',
        'points': 10
    }
}

def add_match(title, opponent, match_date, location, reminder_time=None, created_by=None):
    """添加比赛提醒"""
    session = get_session()
    try:
        # 如果没有设置提醒时间，默认提前1天
        if not reminder_time:
            reminder_time = match_date - timedelta(days=1)
        
        match = MatchReminder(
            title=title,
            opponent=opponent,
            match_date=match_date,
            location=location,
            reminder_time=reminder_time,
            created_by=created_by or st.session_state.user,
            is_completed=False
        )
        session.add(match)
        session.commit()
        
        # 添加积分
        from modules.points import add_points
        add_points(created_by, 10, f'添加了比赛：{title}')
        
        return True
    except Exception as e:
        st.error(f"添加比赛失败：{e}")
        session.rollback()
        return False
    finally:
        session.close()

def get_matches(status=None, days=30):
    """获取比赛列表"""
    session = get_session()
    try:
        query = session.query(MatchReminder)
        
        # 时间范围：最近days天到未来days天
        start_date = datetime.now() - timedelta(days=days)
        end_date = datetime.now() + timedelta(days=days)
        
        query = query.filter(
            MatchReminder.match_date >= start_date,
            MatchReminder.match_date <= end_date
        )
        
        if status == 'upcoming':
            query = query.filter(
                MatchReminder.match_date > datetime.now(),
                MatchReminder.is_completed == False
            )
        elif status == 'completed':
            query = query.filter(MatchReminder.is_completed == True)
        elif status == 'ongoing':
            # 进行中：比赛时间在今天，且未完成
            today_start = datetime.now().replace(hour=0, minute=0, second=0)
            today_end = today_start + timedelta(days=1)
            query = query.filter(
                MatchReminder.match_date >= today_start,
                MatchReminder.match_date <= today_end,
                MatchReminder.is_completed == False
            )
        
        return query.order_by(MatchReminder.match_date).all()
    finally:
        session.close()

def update_match_result(match_id, result_score, notes):
    """更新比赛结果"""
    session = get_session()
    try:
        match = session.query(MatchReminder).filter(MatchReminder.id == match_id).first()
        if match:
            match.is_completed = True
            # 可以添加结果字段，需要先在数据库模型中添加
            # match.result = result_score
            # match.notes = notes
            session.commit()
            
            # 添加积分
            from modules.points import add_points
            add_points(st.session_state.user, 15, f'完成了比赛：{match.title}')
            
            return True
    except Exception as e:
        st.error(f"更新失败：{e}")
        session.rollback()
        return False
    finally:
        session.close()

def get_match_status(match):
    """获取比赛当前状态"""
    now = datetime.now()
    match_date = match.match_date
    
    if match.is_completed:
        return MATCH_STATUS['completed']
    elif match_date.date() < now.date():
        # 过了日期但没标记完成
        return MATCH_STATUS['completed']
    elif match_date.date() == now.date():
        return MATCH_STATUS['ongoing']
    else:
        return MATCH_STATUS['upcoming']

def get_upcoming_reminders():
    """获取需要提醒的比赛"""
    session = get_session()
    try:
        now = datetime.now()
        # 提醒时间在当前时间前后1小时内，且比赛未开始
        matches = session.query(MatchReminder).filter(
            MatchReminder.reminder_time >= now - timedelta(hours=1),
            MatchReminder.reminder_time <= now + timedelta(hours=1),
            MatchReminder.match_date > now,
            MatchReminder.is_completed == False
        ).all()
        return matches
    finally:
        session.close()

def render_tasks():
    """渲染赛事任务界面"""
    st.markdown("""
    <div style='text-align: center; padding: 20px;'>
        <h1 style='color: white;'>🏆 赛事任务</h1>
        <p style='color: rgba(255,255,255,0.8);'>记录每一场精彩比赛，做最棒的场边指导</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 检查是否有需要提醒的比赛
    upcoming_reminders = get_upcoming_reminders()
    if upcoming_reminders:
        for match in upcoming_reminders:
            st.warning(f"""
            ⏰ **比赛即将开始！**
            - {match.title} vs {match.opponent}
            - 时间：{match.match_date.strftime('%m-%d %H:%M')}
            - 地点：{match.location}
            
            记得给男朋友加油哦！ 💪
            """)
    
    # 创建标签页
    tab1, tab2, tab3 = st.tabs(["📅 赛程表", "➕ 添加比赛", "📊 比赛统计"])
    
    # ========== 标签页1：赛程表 ==========
    with tab1:
        # 筛选器
        col1, col2 = st.columns(2)
        with col1:
            filter_status = st.selectbox(
                "筛选状态",
                options=['all', 'upcoming', 'ongoing', 'completed'],
                format_func=lambda x: {
                    'all': '全部比赛',
                    'upcoming': '即将开始',
                    'ongoing': '进行中',
                    'completed': '已结束'
                }[x]
            )
        
        with col2:
            days_range = st.selectbox(
                "时间范围",
                options=[7, 14, 30, 60],
                format_func=lambda x: f'最近 {x} 天'
            )
        
        # 获取比赛列表
        status = None if filter_status == 'all' else filter_status
        matches = get_matches(status, days_range)
        
        if matches:
            # 按日期分组显示
            current_month = None
            for match in matches:
                match_date = match.match_date
                month_key = match_date.strftime('%Y年%m月')
                
                # 显示月份分隔
                if month_key != current_month:
                    current_month = month_key
                    st.markdown(f"### 📅 {month_key}")
                
                # 获取比赛状态
                status_info = get_match_status(match)
                
                # 创建比赛卡片
                with st.container():
                    # 根据状态设置边框颜色
                    st.markdown(f"""
                    <div style='
                        background: {status_info["color"]}10;
                        border-left: 4px solid {status_info["color"]};
                        border-radius: 10px;
                        padding: 15px;
                        margin: 10px 0;
                    '>
                        <div style='display: flex; justify-content: space-between; align-items: center;'>
                            <div>
                                <span style='font-size: 1.2em; font-weight: bold;'>{match.title}</span>
                                <span style='margin-left: 10px; color: gray;'>vs {match.opponent}</span>
                            </div>
                            <span style='background: {status_info["color"]}; color: white; padding: 3px 10px; border-radius: 15px; font-size: 0.9em;'>
                                {status_info["emoji"]} {status_info["name"]}
                            </span>
                        </div>
                        
                        <div style='display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin: 15px 0;'>
                            <div>
                                <span style='color: gray;'>📅 时间</span><br>
                                <span>{match_date.strftime('%m/%d %H:%M')}</span>
                            </div>
                            <div>
                                <span style='color: gray;'>📍 地点</span><br>
                                <span>{match.location}</span>
                            </div>
                            <div>
                                <span style='color: gray;'>⏰ 提醒</span><br>
                                <span>{match.reminder_time.strftime('%m/%d %H:%M') if match.reminder_time else '未设置'}</span>
                            </div>
                        </div>
                        
                        <div style='display: flex; justify-content: space-between; align-items: center;'>
                            <span style='color: gray;'>创建者：{'💕 我' if match.created_by == 'me' else '🏸 他'}</span>
                            {f'<span style="color: gold;">🏆 已结束</span>' if match.is_completed else ''}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # 如果是进行中或已结束，显示操作按钮
                    if status_info['name'] == MATCH_STATUS['ongoing']['name']:
                        col_a, col_b = st.columns(2)
                        with col_a:
                            if st.button(f"💪 加油助威", key=f"cheer_{match.id}"):
                                st.session_state['cheer_match'] = match.id
                                st.rerun()
                        with col_b:
                            if st.button(f"🏁 记录结果", key=f"result_{match.id}"):
                                st.session_state['result_match'] = match.id
                                st.rerun()
                    
                    elif status_info['name'] == MATCH_STATUS['completed']['name'] and not match.is_completed:
                        if st.button(f"✅ 标记已完成", key=f"complete_{match.id}"):
                            if update_match_result(match.id, "", ""):
                                st.success("比赛已标记完成！")
                                st.rerun()
        else:
            st.info("暂无比赛记录，去添加一场吧！")
    
    # ========== 标签页2：添加比赛 ==========
    with tab2:
        st.markdown("""
        <div class='court-card'>
            <h3>➕ 添加新比赛</h3>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("add_match_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                title = st.text_input("🏸 比赛名称", placeholder="例：市羽毛球公开赛")
                opponent = st.text_input("🎯 对手", placeholder="例：XX俱乐部")
                location = st.text_input("📍 比赛地点", placeholder="例：XX体育馆")
            
            with col2:
                match_date = st.date_input("📅 比赛日期", min_value=date.today())
                match_time = st.time_input("⏰ 比赛时间", value=datetime.now().time())
                reminder = st.checkbox("设置提醒", value=True)
            
            if reminder:
                reminder_days = st.number_input("提前几天提醒", min_value=0, max_value=7, value=1)
                reminder_time = st.time_input("提醒时间", value=datetime.now().time().replace(hour=9, minute=0))
                
                # 组合提醒时间
                reminder_datetime = datetime.combine(
                    match_date - timedelta(days=reminder_days),
                    reminder_time
                )
            else:
                reminder_datetime = None
            
            # 合并日期和时间
            match_datetime = datetime.combine(match_date, match_time)
            
            submitted = st.form_submit_button("✅ 添加比赛", use_container_width=True)
            if submitted and title and opponent and location:
                if add_match(title, opponent, match_datetime, location, reminder_datetime):
                    st.success("🎉 比赛添加成功！记得准时加油哦~")
                    st.rerun()
    
    # ========== 标签页3：比赛统计 ==========
    with tab3:
        st.markdown("""
        <div class='court-card'>
            <h3>📊 比赛统计</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # 获取所有比赛
        all_matches = get_matches(days=90)
        
        if all_matches:
            # 转换为DataFrame
            matches_data = []
            for m in all_matches:
                matches_data.append({
                    '日期': m.match_date,
                    '比赛': m.title,
                    '对手': m.opponent,
                    '地点': m.location,
                    '状态': '已完成' if m.is_completed else '未完成',
                    '创建者': '我' if m.created_by == 'me' else '他'
                })
            
            df = pd.DataFrame(matches_data)
            
            # 统计卡片
            total_matches = len(df)
            completed = len(df[df['状态'] == '已完成'])
            upcoming = len(df[df['match_date'] > datetime.now()])
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("总比赛数", total_matches)
            with col2:
                st.metric("已完成", completed)
            with col3:
                st.metric("完成率", f"{(completed/total_matches*100):.1f}%" if total_matches > 0 else "0%")
            with col4:
                st.metric("即将进行", upcoming)
            
            # 月度比赛分布图
            st.markdown("### 📅 月度比赛分布")
            
            # 按月份统计
            df['月份'] = df['日期'].dt.strftime('%Y-%m')
            monthly_stats = df.groupby('月份').size().reset_index(name='数量')
            
            fig = go.Figure(data=[
                go.Bar(
                    x=monthly_stats['月份'],
                    y=monthly_stats['数量'],
                    marker_color='#ff69b4',
                    text=monthly_stats['数量'],
                    textposition='auto'
                )
            ])
            
            fig.update_layout(
                title="每月比赛数量",
                plot_bgcolor='rgba(27, 77, 27, 0.3)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white'),
                xaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
                yaxis=dict(gridcolor='rgba(255,255,255,0.1)', title="比赛场次")
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # 最近比赛列表
            st.markdown("### 📋 最近比赛记录")
            st.dataframe(
                df[['日期', '比赛', '对手', '地点', '状态']].sort_values('日期', ascending=False).head(10),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("还没有比赛记录，去添加第一场比赛吧！")
    
    # ========== 助威弹窗 ==========
    if 'cheer_match' in st.session_state:
        match_id = st.session_state['cheer_match']
        match = next((m for m in get_matches() if m.id == match_id), None)
        
        if match:
            with st.expander("💪 为比赛加油", expanded=True):
                st.markdown(f"""
                ### {match.title} vs {match.opponent}
                比赛时间：{match.match_date.strftime('%Y-%m-%d %H:%M')}
                """)
                
                cheer_type = st.selectbox(
                    "选择助威方式",
                    options=list(CHEER_TYPES.keys()),
                    format_func=lambda x: f"{CHEER_TYPES[x]['emoji']} {CHEER_TYPES[x]['name']} (+{CHEER_TYPES[x]['points']}默契值)"
                )
                
                message = st.text_area("想说的话", placeholder="加油！你是最棒的！")
                
                if st.button("💝 发送助威", use_container_width=True):
                    # 记录助威并获得积分
                    from modules.points import add_points
                    add_points(st.session_state.user, CHEER_TYPES[cheer_type]['points'], 
                              f'为{match.title}比赛助威')
                    st.success(f"✨ 助威成功！获得{CHEER_TYPES[cheer_type]['points']}默契值")
                    
                    # 如果是惊喜到场，额外提醒
                    if cheer_type == 'surprise':
                        st.balloons()
                        st.info("🎊 惊喜准备中...记得准时出现给他一个惊喜！")
                    
                    del st.session_state['cheer_match']
                    st.rerun()