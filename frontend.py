# frontend.py

import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import plotly.express as px
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure page
st.set_page_config(
    page_title="Email Summarizer Dashboard",
    page_icon="📧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Backend API configuration
BACKEND_URL = os.getenv("BACKEND_URL")

def check_backend_connection():
    """Check if backend API is available"""
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        return response.status_code == 200, response.json()
    except requests.exceptions.RequestException:
        return False, None

@st.cache_data(ttl=1000)  # Cache for 5 minutes
def load_email_data():
    """Load email data from backend API"""
    try:
        response = requests.get(f"{BACKEND_URL}/process-unread-emails", timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Error connecting to backend: {e}")
        return None

def trigger_manual_summary():
    """Trigger manual processing of unread emails"""
    try:
        with st.spinner("Checking for unread emails..."):
            response = requests.get(f"{BACKEND_URL}/process-unread-emails", timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if result['count'] > 0:
                    st.success(f"✅ Processed {result['count']} emails")
                    st.balloons()
                    st.session_state.last_processed = result
                    return True
                else:
                    st.info("📭 No unread emails found")
                    return False
            else:
                st.error(f"Error: {response.json().get('detail', 'Unknown error')}")
                return False
    except requests.exceptions.RequestException as e:
        st.error(f"Connection error: {e}")
        return False

def create_sample_data():
    """Create sample data for demo purposes"""
    return {
        'Timestamp': [datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
        'Sender': ['john@example.com\njane@example.com'],
        'Subject': ['Meeting Tomorrow\nProject Update'],
        'Email': ['Please confirm your attendance for tomorrow...\n\nThe project status has been updated...'],
        'Summary': ['Two emails received: 1) John requesting meeting confirmation for tomorrow 2) Jane providing project status update. Both require responses.']
    }
    
def main():
    """Main Streamlit application"""
    
    # Header
    st.title("📧 Email Summarizer Dashboard")
    st.markdown("---")
    
    # Check backend connection in sidebar
    with st.sidebar:
        st.header("🔧 System Status")
        
        backend_ok, health_data = check_backend_connection()
        
        if not backend_ok:
            st.error("Backend Connection Issues:")
            st.write("Could not connect to the Email Summarizer API")
            st.info("Make sure the backend is running:")
            st.code("python main.py", language="bash")
        else:
            st.success("✅ Backend Connection OK")
            if health_data:
                st.write(f"**Gmail Status:** {health_data['services']['gmail']}")
                st.write(f"**Sheets Status:** {health_data['services']['sheets']}")
        
        st.markdown("---")
        
        # Manual trigger
        st.header("⚡ Manual Actions")
        
        if st.button("📥 Check New Emails", type="primary"):
            if backend_ok:
                if trigger_manual_summary():
                    st.cache_data.clear()
                    st.rerun()
            else:
                st.error("Please fix backend connection first")
        
        # Refresh data
        if st.button("🔄 Refresh Data"):
            st.cache_data.clear()
            st.rerun()
        
        # Demo mode toggle
        st.markdown("---")
        st.header("🎮 Demo Mode")
        demo_mode = st.checkbox("Use demo data", value=False)
        
        st.markdown("---")
    
    # Main content
    if not backend_ok and not demo_mode:
        st.warning("⚠️ Please ensure the backend API is running to use this dashboard, or enable demo mode.")
        return
    
    # Load data
    if demo_mode:
        data = create_sample_data()
        df = pd.DataFrame(data)
    else:
        with st.spinner("Loading email data..."):
            data = load_email_data()
        
        if not data or data.get('count', 0) == 0:
            st.info("📭 No processed emails found. The system will automatically process new emails when they arrive.")
            return
        
        # Create DataFrame from API response
        df = pd.DataFrame([{
            'Timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'Sender': '\n'.join(data.get('senders', [])),
            'Subject': 'Combined Summary',
            'Email': 'Multiple emails processed',
            'Summary': data.get('summary', 'No summary available')
        }])
    
    # Statistics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        email_count = len(df.iloc[0]['Sender'].split('\n')) if len(df) > 0 else 0
        st.metric("Emails Processed", email_count)
    
    with col2:
        unique_senders = len(set(df.iloc[0]['Sender'].split('\n'))) if len(df) > 0 else 0
        st.metric("Unique Senders", unique_senders)
    
    with col3:
        today_emails = email_count  # Simplified for demo
        st.metric("Today's Emails", today_emails)
    
    with col4:
        avg_length = len(df.iloc[0]['Summary']) if len(df) > 0 else 0
        st.metric("Summary Length", f"{avg_length} chars")
    
    st.markdown("---")
    
    # Tabs for different views
    tab1, tab2 = st.tabs(["📋 Email Details", "📊 Analytics"])
    
    with tab1:
        st.header("Email Summaries")
        
        if len(df) > 0:
            # Display each batch
            for idx, row in df.iterrows():
                with st.expander(f"📧 Batch Summary - {row['Timestamp']}", expanded=True):
                    senders = row['Sender'].split('\n') if row['Sender'] else []
                    st.write(f"**Processed {len(senders)} emails**")
                    
                    # Display senders
                    st.write("**Senders:**")
                    for sender in senders:
                        if sender.strip():
                            st.write(f"• {sender}")
                    
                    # Display summary
                    st.write("**Combined Summary:**")
                    st.write(row['Summary'])
                    
                    # Option to view details
                    if st.checkbox("Show email details", key=f"details_{idx}"):
                        if 'Subject' in row and row['Subject'] != 'Combined Summary':
                            subjects = row['Subject'].split('\n')
                            st.write("**Subjects:**")
                            for subject in subjects:
                                if subject.strip():
                                    st.write(f"• {subject}")
                        
                        if 'Email' in row and row['Email'] != 'Multiple emails processed':
                            st.write("**Email Content:**")
                            st.text_area("", value=row['Email'], height=200, disabled=True)
        else:
            st.info("No email data available")
                            
    with tab2:
        st.header("Email Analytics")
        
        if len(df) > 0:
            # Sample visualization
            st.write("### Email Activity Over Time")
            
            # Create sample time series data
            dates = pd.date_range(end=datetime.today(), periods=7).date
            sample_data = pd.DataFrame({
                'date': dates,
                'count': [3, 5, 2, 7, 4, 6, 5]
            })
            
            fig_timeline = px.line(sample_data, x='date', y='count', 
                                 title="Emails per Day",
                                 markers=True)
            st.plotly_chart(fig_timeline, use_container_width=True)
            
            # Sender distribution
            if len(df) > 0 and df.iloc[0]['Sender']:
                st.write("### Sender Distribution")
                senders = df.iloc[0]['Sender'].split('\n')
                sender_counts = {}
                for sender in senders:
                    if sender.strip():
                        sender_counts[sender] = sender_counts.get(sender, 0) + 1
                
                if sender_counts:
                    sender_df = pd.DataFrame(list(sender_counts.items()), 
                                           columns=['sender', 'count'])
                    fig_senders = px.pie(sender_df, values='count', names='sender',
                                       title="Email Distribution by Sender")
                    st.plotly_chart(fig_senders, use_container_width=True)
        else:
            st.info("Not enough data for analytics")
    
    # Footer
    st.markdown("---")
    st.markdown(f"*Email Summarizer Dashboard - Backend: {BACKEND_URL}*")

if __name__ == "__main__":
    main()

