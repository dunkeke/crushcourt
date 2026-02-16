"""
健康管理模块 - 喝水吃饭提醒
功能：
- 设置定时提醒（喝水/早餐/午餐/晚餐/睡觉）
- 记录完成情况
- 积分奖励
- 健康统计
"""
import streamlit as st
import pandas as pd
from datetime import datetime, time, timedelta
from modules import get_session, HealthReminder, HealthLog
import plotly.graph_objects as go
import plotly.express as px

# 提醒类型配置
REMINDER_TYPES = {
    'water': {
        'name': '💧 喝水',
        'emoji': '💧',
        'color': '#00CED1',
        'default_message': '亲爱的，该喝水啦！💧',
        'points': 2,
        'icon': '🥤'
    },
    'breakfast': {
        'name': '🍳 早餐',
        'emoji': '🍳',
        'color': '#FFA500',
        'default_message': '记得吃早餐，开启元气满满的一天！☀️',
        'points': 3,
        'icon': '🥐'
    },
    'lunch': {
        'name': '🍱 午餐',
        'emoji': '🍱',
        'color': '#FF6B6B',
        'default_message': '该吃午餐啦，要好好吃饭哦！🍚',
        'points': 3,
        'icon': '🍜'
    },
    'dinner': {
        'name': '🍽️ 晚餐',
        'emoji': '🍽️',
        'color': '#4ECDC4',
        'default_message': '晚餐时间到，记得按时吃饭！🌙',
        'points': 3,
        'icon': '🍲'
    },
    'sleep': {
        'name': '😴 睡觉',
        'emoji': '😴',
        'color': '#9B59B6',
        'default_message': '早点休息，晚安好梦~ 💤',
        'points': 4,
        'icon': '🛏️'
    }
}

def get_reminders(user=None, active_only=True):
    """获取提醒设置"""
    session = get_session()
    try:
        query = session.query(HealthReminder)
        if user:
            query = query.filter(HealthReminder.set_by == user)
        if active_only:
            query = query.filter(HealthReminder.is_active == True)
        return query.all()
    finally:
        session.close()

def add_reminder(reminder_type, reminder_time, custom_message=None, set_by=None):
    """添加新提醒"""
    session = get_session()
    try:
        # 使用默认消息或自定义消息
        message = custom_message if custom_message else REMINDER_TYPES[reminder_type]['default_message']
        
        reminder = HealthReminder(
            reminder_type=reminder_type,
            reminder_time=reminder_time.strftime("%H:%M"),
            message=message,
            set_by=set_by or st.session_state.user,
            is_active=True
        )
        session.add(reminder)
        session.commit()
        
        # 添加积分
        from modules.points import add_points
        add_points(set_by, 2, f'设置了{REMINDER_TYPES[reminder_type]["name"]}提醒')
        
        return True
    except Exception as e:
        st.error(f"设置提醒失败：{e}")
        session.rollback()
        return False
    finally:
        session.close()

def delete_reminder(reminder_id):
    """删除提醒"""
    session = get_session()
    try:
        reminder = session.query(HealthReminder).filter(HealthReminder.id == reminder_id).first()
        if reminder:
            session.delete(reminder)
            session.commit()
            return True
    except Exception as e:
        st.error(f"删除失败：{e}")
        session.rollback()
        return False
    finally:
        session.close()

def toggle_reminder(reminder_id, is_active):
    """启用/禁用提醒"""
    session = get_session()
    try:
        reminder = session.query(HealthReminder).filter(HealthReminder.id == reminder_id).first()
        if reminder:
            reminder.is_active = is_active
            session.commit()
            return True
    except Exception as e:
        st.error(f"操作失败：{e}")
        session.rollback()
        return False
    finally:
        session.close()

def log_completion(reminder_id, user, note=None):
    """记录完成提醒"""
    session = get_session()
    try:
        log = HealthLog(
            reminder_id=reminder_id,
            user=user,
            completed_at=datetime.now(),
            note=note
        )
        session.add(log)
        
        # 获取提醒类型以确定积分
        reminder = session.query(HealthReminder).filter(HealthReminder.id == reminder_id).first()
        if reminder:
            points = REMINDER_TYPES[reminder.reminder_type]['points']
            
            # 添加积分
            from modules.points import add_points
            add_points(user, points, f'完成了{REMINDER_TYPES[reminder.reminder_type]["name"]}提醒')
        
        session.commit()
        return True
    except Exception as e:
        st.error(f"记录失败：{e}")
        session.rollback()
        return False
    finally:
        session.close()

def get_today_completions(user):
    """获取用户今天的完成记录"""
    session = get_session()
    try:
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        
        completions = session.query(HealthLog).filter(
            HealthLog.user == user,
            HealthLog.completed_at >= today_start,
            HealthLog.completed_at < today_end
        ).all()
        
        # 获取对应的提醒信息
        result = []
        for comp in completions:
            reminder = session.query(HealthReminder).filter(HealthReminder.id == comp.reminder_id).first()
            if reminder:
                result.append({
                    'id': comp.id,
                    'reminder_type': reminder.reminder_type,
                    'completed_at': comp.completed_at,
                    'note': comp.note
                })
        return result
    finally:
        session.close()

def check_reminder_due(reminder):
    """检查提醒是否到时间（且今天未完成）"""
    now = datetime.now()
    reminder_time = datetime.strptime(reminder.reminder_time, "%H:%M").time()
    reminder_datetime = now.replace(hour=reminder_time.hour, minute=reminder_time.minute, second=0)
    
    # 如果提醒时间已经过了今天的时间，算作明天
    if reminder_datetime > now:
        return False
    
    # 检查今天是否已经完成
    completions = get_today_completions(reminder.set_by)
    completed_types = [c['reminder_type'] for c in completions]
    
    return reminder.reminder_type not in completed_types

def render_health():
    """渲染健康管理界面"""
    st.markdown("""
    <div style='text-align: center; padding: 20px;'>
        <h1 style='color: white;'>💧 健康管理</h1>
        <p style='color: rgba(255,255,255,0.8);'>互相提醒，一起健康生活</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 创建两列布局
    col1, col2 = st.columns([3, 2])
    
    with col1:
        # ========== 今日健康卡片 ==========
        st.markdown("""
        <div class='court-card'>
            <h3>📅 今日健康任务</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # 获取今天的完成情况
        today_completions = get_today_completions(st.session_state.user)
        completed_types = [c['reminder_type'] for c in today_completions]
        
        # 获取所有活跃提醒
        reminders = get_reminders()
        
        if reminders:
            for reminder in reminders:
                reminder_config = REMINDER_TYPES[reminder.reminder_type]
                is_completed = reminder.reminder_type in completed_types
                
                # 找到对应的完成记录
                completion = next((c for c in today_completions if c['reminder_type'] == reminder.reminder_type), None)
                
                # 检查是否到时间
                is_due = check_reminder_due(reminder)
                
                # 卡片样式
                if is_completed:
                    status_color = "#4CAF50"
                    status_text = "✅ 已完成"
                    border_color = "#4CAF50"
                elif is_due:
                    status_color = "#FFA500"
                    status_text = "⏰ 待完成"
                    border_color = "#FFA500"
                else:
                    status_color = "#808080"
                    status_text = "⏳ 未到时间"
                    border_color = "#808080"
                
                st.markdown(f"""
                <div style='
                    background: {reminder_config["color"]}10;
                    border-left: 4px solid {border_color};
                    padding: 15px;
                    margin: 10px 0;
                    border-radius: 10px;
                '>
                    <div style='display: flex; justify-content: space-between; align-items: center;'>
                        <div>
                            <span style='font-size: 1.2em;'>{reminder_config["icon"]} {reminder_config["name"]}</span>
                            <span style='color: gray; margin-left: 10px;'>{reminder.reminder_time}</span>
                        </div>
                        <span style='color: {status_color}; font-weight: bold;'>{status_text}</span>
                    </div>
                    <div style='margin: 10px 0; color: white;'>
                        💬 {reminder.message}
                    </div>
                    <div style='display: flex; justify-content: space-between; align-items: center;'>
                        <span style='color: gray;'>设置者：{'💕 我' if reminder.set_by == 'me' else '🏸 他'}</span>
                        <span style='color: gold;'>+{reminder_config["points"]} 默契值</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # 如果是待完成状态，显示完成按钮
                if is_due and not is_completed:
                    if st.button(f"✅ 标记完成 - {reminder_config['name']}", 
                               key=f"complete_{reminder.id}",
                               use_container_width=True):
                        note = st.text_input("添加备注（可选）", key=f"note_{reminder.id}")
                        if log_completion(reminder.id, st.session_state.user, note):
                            st.success(f"🎉 太棒了！获得{reminder_config['points']}默契值")
                            st.rerun()
        else:
            st.info("还没有设置提醒，快去添加吧！")
    
    with col2:
        # ========== 设置新提醒 ==========
        st.markdown("""
        <div class='court-card'>
            <h3>⚙️ 设置新提醒</h3>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("new_reminder"):
            # 提醒类型
            reminder_type = st.selectbox(
                "提醒类型",
                options=list(REMINDER_TYPES.keys()),
                format_func=lambda x: f"{REMINDER_TYPES[x]['icon']} {REMINDER_TYPES[x]['name']}"
            )
            
            # 提醒时间
            reminder_time = st.time_input(
                "提醒时间",
                value=time(9, 0)  # 默认早上9点
            )
            
            # 自定义消息
            default_msg = REMINDER_TYPES[reminder_type]['default_message']
            custom_message = st.text_input(
                "提醒内容（可选）",
                placeholder=default_msg,
                help=f"默认：{default_msg}"
            )
            
            # 设置给谁（固定是对方）
            set_for = st.radio(
                "提醒对象",
                options=['对方', '自己'],
                horizontal=True,
                help="可以选择提醒对方或提醒自己"
            )
            
            submitted = st.form_submit_button("💝 设置提醒", use_container_width=True)
            if submitted:
                target_user = 'him' if st.session_state.user == 'me' else 'me' if set_for == '对方' else st.session_state.user
                if add_reminder(reminder_type, reminder_time, custom_message, target_user):
                    st.success("✅ 提醒设置成功！")
                    st.rerun()
        
        # ========== 我的提醒列表 ==========
        st.markdown("---")
        st.markdown("### 📋 我的提醒设置")
        
        my_reminders = get_reminders(st.session_state.user)
        if my_reminders:
            for reminder in my_reminders:
                reminder_config = REMINDER_TYPES[reminder.reminder_type]
                with st.container():
                    col_a, col_b = st.columns([3, 1])
                    with col_a:
                        st.markdown(f"""
                        {reminder_config['icon']} **{reminder_config['name']}** {reminder.reminder_time}
                        """)
                    with col_b:
                        # 开关按钮
                                        if st.button("❌ 删除", key=f"del_{reminder.id}"):
                            if delete_reminder(reminder.id):
                                st.success("删除成功")
                                st.rerun()
        else:
            st.info("还没有设置提醒")
        
        # ========== 健康统计 ==========
        st.markdown("---")
        st.markdown("### 📊 本周健康统计")
        
        # 获取双方本周完成情况
        me_completions = get_today_completions('me')
        him_completions = get_today_completions('him')
        
        # 简单的统计图表
        stats_data = {
            '类型': ['喝水', '早餐', '午餐', '晚餐', '睡觉'],
            '我': [
                sum(1 for c in me_completions if c['reminder_type'] == 'water'),
                sum(1 for c in me_completions if c['reminder_type'] == 'breakfast'),
                sum(1 for c in me_completions if c['reminder_type'] == 'lunch'),
                sum(1 for c in me_completions if c['reminder_type'] == 'dinner'),
                sum(1 for c in me_completions if c['reminder_type'] == 'sleep')
            ],
            '他': [
                sum(1 for c in him_completions if c['reminder_type'] == 'water'),
                sum(1 for c in him_completions if c['reminder_type'] == 'breakfast'),
                sum(1 for c in him_completions if c['reminder_type'] == 'lunch'),
                sum(1 for c in him_completions if c['reminder_type'] == 'dinner'),
                sum(1 for c in him_completions if c['reminder_type'] == 'sleep')
            ]
        }
        
        df_stats = pd.DataFrame(stats_data)
        
        # 创建柱状图
        fig = go.Figure(data=[
            go.Bar(name='我', x=df_stats['类型'], y=df_stats['我'], 
                   marker_color='#ff69b4', text=df_stats['我'], textposition='auto'),
            go.Bar(name='他', x=df_stats['类型'], y=df_stats['他'], 
                   marker_color='#4169e1', text=df_stats['他'], textposition='auto')
        ])
        
        fig.update_layout(
            title="今日完成情况",
            plot_bgcolor='rgba(27, 77, 27, 0.3)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            barmode='group',
            xaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
            yaxis=dict(gridcolor='rgba(255,255,255,0.1)', title="完成次数")
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # 默契值提示
        total_points = sum(REMINDER_TYPES[c['reminder_type']]['points'] for c in me_completions)
        if total_points > 0:
            st.success(f"🎯 今天已获得 {total_points} 默契值！")