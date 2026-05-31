import streamlit as st
import os
import pandas as pd
from dotenv import load_dotenv
from processor import create_knowledge_base, load_knowledge_base
from chatbot_engine import create_chatbot, get_answer

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

st.set_page_config(
    page_title="SVIMS CampusBot",
    page_icon="🎓",
    layout="wide"
)

st.markdown("""
<style>
.user-msg {
    background-color: #1a237e;
    color: white;
    padding: 12px 18px;
    border-radius: 18px 18px 5px 18px;
    margin: 8px 0;
    max-width: 75%;
    float: right;
    clear: both;
}
.bot-msg {
    background-color: #f5f5f5;
    color: #333;
    padding: 12px 18px;
    border-radius: 18px 18px 18px 5px;
    margin: 8px 0;
    max-width: 75%;
    float: left;
    clear: both;
    border-left: 4px solid #ff6f00;
}
.clearfix { clear: both; }
.error-box {
    background-color: #ffebee;
    border: 1px solid #ef9a9a;
    border-radius: 8px;
    padding: 10px 15px;
    color: #c62828;
    margin: 10px 0;
}
</style>
""", unsafe_allow_html=True)

# =============================================
# SESSION STATE
# =============================================
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "chain" not in st.session_state:
    st.session_state.chain = None
if "ready" not in st.session_state:
    st.session_state.ready = False
if "auto_question" not in st.session_state:
    st.session_state.auto_question = None
if "load_error" not in st.session_state:
    st.session_state.load_error = None

# =============================================
# KNOWLEDGE BASE LOAD
# =============================================
if not st.session_state.ready and st.session_state.load_error is None:
    with st.spinner("🎓 SVIMS CampusBot loading..."):
        try:
            vector_store = load_knowledge_base()
            if vector_store is None:
                st.info("🔄 Knowledge base nahi mili, nai bana raha hoon... (1-2 min)")
                vector_store = create_knowledge_base()
            st.session_state.chain = create_chatbot(vector_store)
            st.session_state.ready = True
            st.session_state.load_error = None
        except Exception as e:
            error_msg = str(e)
            print(f"🚨 Startup Error: {error_msg}")
            st.session_state.load_error = error_msg
            st.session_state.ready = False

# Show load error if any
if st.session_state.load_error:
    st.markdown(f"""
    <div class="error-box">
    ❌ <b>Startup Error:</b> {st.session_state.load_error}<br><br>
    <b>Possible fixes:</b><br>
    1. Check your <code>.env</code> file has correct GROQ_API_KEY<br>
    2. Make sure <code>faiss_index</code> folder exists or run <code>python processor.py</code><br>
    3. Check all dependencies installed: <code>pip install -r requirements.txt</code>
    </div>
    """, unsafe_allow_html=True)
    if st.button("🔄 Retry"):
        st.session_state.load_error = None
        st.rerun()

# =============================================
# AUTO QUESTION HANDLER
# =============================================
if st.session_state.auto_question and st.session_state.ready:
    q = st.session_state.auto_question
    st.session_state.auto_question = None
    st.session_state.chat_history.append({"role": "user", "content": q})
    with st.spinner("🤔 Finding answer..."):
        try:
            answer = get_answer(st.session_state.chain, q)
        except Exception as e:
            print(f"Auto-question error: {e}")
            answer = "Something went wrong. Please contact svimi@svimi.org"
    st.session_state.chat_history.append({"role": "bot", "content": answer})
    st.rerun()

# =============================================
# SIDEBAR
# =============================================
with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding:10px;
    background:linear-gradient(135deg,#1a237e,#283593);
    border-radius:10px; margin-bottom:10px;">
    <img src="https://www.svimi.org/assets/images/svimsi-logo.png"
    width="120" style="border-radius:50%;
    background:white; padding:5px;"/>
    <h3 style="color:white; margin:5px 0;">CampusBot</h3>
    <p style="color:#ffcc80; font-size:12px; margin:0;">SVIMS Indore</p>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.ready:
        st.success("🟢 Bot Active")
    elif st.session_state.load_error:
        st.error("🔴 Error - Check API Key")
    else:
        st.warning("⏳ Loading...")

    st.divider()

    tab1, tab2, tab3, tab4 = st.tabs(["💬 Chat", "📞 Contacts", "📅 Calendar", "🗺️ Map"])

    with tab1:
        st.markdown("**Search & Filter**")
        search_query = st.text_input("Search...", placeholder="e.g. library, fees")
        filter_category = st.selectbox(
            "Category:",
            ["All", "Academics", "Placement", "Facilities",
             "Clubs & Events", "Faculty", "Fees", "Admission"]
        )
        if st.button("🔍 Search", type="primary", use_container_width=True):
            if search_query:
                q = f"{filter_category}: {search_query}" if filter_category != "All" else search_query
                st.session_state.auto_question = q
                st.rerun()

        st.markdown("**Quick Questions**")
        quick_qs = {
            "🎓 Academics": [
                "Tell me about BCA program",
                "What is the attendance policy?",
                "What courses does SVIMS offer?"
            ],
            "💼 Placement": [
                "Tell me about Placement Cell",
                "Top recruiters at SVIMS?",
                "Placement statistics?"
            ],
            "🏛️ Facilities": [
                "What are library timings?",
                "Tell me about hostels",
                "What facilities are available?"
            ],
            "👨‍🏫 Faculty": [
                "Who is the Director?",
                "Department heads info?",
                "HOD of Computer Science?"
            ],
            "💰 Fees": [
                "What is the fee structure?",
                "Scholarship information?"
            ],
            "🎭 Clubs": [
                "What clubs are available?",
                "When is Prabandhotsav?",
                "Tell me about EDC Cell"
            ]
        }
        for category, questions in quick_qs.items():
            with st.expander(category):
                for q in questions:
                    if st.button(q, key=f"q_{q}", use_container_width=True):
                        st.session_state.auto_question = q
                        st.rerun()

    with tab2:
        st.markdown("**📞 Contact Directory**")
        st.markdown("""
        **Main Office**
        📧 [svimi@svimi.org](mailto:svimi@svimi.org)
        📞 [+91-731-2789925](tel:+917312789925)
        🆓 [1800-233-2601](tel:18002332601)

        **Admission**
        📧 [admission@svimi.org](mailto:admission@svimi.org)
        📞 [9329912587](tel:9329912587)
        💬 [WhatsApp](https://wa.me/919329912587)

        **Director**
        👤 Dr. George Thomas
        📞 [9425900016](tel:9425900016)

        **Departments**
        📞 CS Dept: [9406803431](tel:9406803431)
        📞 Mgmt UG: [9399576967](tel:9399576967)
        📞 Mgmt PG: [9981612347](tel:9981612347)

        **Emergency**
        🏥 Medical: [9301527178](tel:9301527178)
        📞 Student Welfare: [7312580137](tel:7312580137)
        📞 Exam Cell: [7312518030](tel:7312518030)
        """)

        if st.button("📋 Ask about faculty", use_container_width=True):
            st.session_state.auto_question = "Tell me about SVIMS faculty members"
            st.rerun()

        contacts_data = {
            "Department": ["Main", "Admission", "Director", "CS Dept",
                           "Mgmt UG", "Mgmt PG", "Exam", "Welfare"],
            "Contact": ["svimi@svimi.org", "admission@svimi.org",
                        "Dr. George Thomas", "Dr. Kshama Paithankar",
                        "Dr. Deepa Katiyal", "Dr. Mandip Gill",
                        "Exam Controller", "Student Welfare"],
            "Phone": ["+91-731-2789925", "9329912587", "9425900016",
                      "9406803431", "9399576967", "9981612347",
                      "7312518030", "7312580137"]
        }
        df = pd.DataFrame(contacts_data)
        st.download_button(
            "📥 Download Contacts",
            df.to_csv(index=False),
            "svims_contacts.csv",
            "text/csv",
            use_container_width=True
        )

    with tab3:
        st.markdown("**📅 Academic Calendar 2025-26**")
        st.markdown("""
        | Month | Event |
        |-------|-------|
        | July | New admissions open |
        | August | Academic year starts |
        | August | Abhisanskaran (Induction) |
        | Oct-Nov | Internal exams |
        | November | Srijan event |
        | December | Semester end |
        | January | Khelotsav (Sports) |
        | January | New semester begins |
        | February | Technova / Nav Udyami |
        | March | Prabandhotsav (Annual Fest) |
        | March | Confluence (Alumni Meet) |
        | Apr-May | Final exams |
        | May | Results declared |
        """)

        events_data = {
            "Event": ["Abhisanskaran", "Internal Exams", "Srijan",
                      "Khelotsav", "Nav Udyami", "Prabandhotsav",
                      "Confluence", "Final Exams"],
            "Month": ["August", "Oct-Nov", "November",
                      "January", "February", "March",
                      "March", "Apr-May"],
            "Type": ["Induction", "Academics", "Cultural",
                     "Sports", "Entrepreneurship", "Annual Fest",
                     "Alumni", "Academics"]
        }
        df_events = pd.DataFrame(events_data)
        st.download_button(
            "📥 Download Calendar",
            df_events.to_csv(index=False),
            "svims_calendar.csv",
            "text/csv",
            use_container_width=True
        )

        if st.button("📅 Ask about events", use_container_width=True):
            st.session_state.auto_question = "What are the major events at SVIMS?"
            st.rerun()

    with tab4:
        st.markdown("**📍 SVIMS Location**")
        st.markdown("Scheme No.71, Gumasta Nagar, Indore - 452009, MP")

        st.markdown("""
        <iframe
        src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3679.8!2d75.8577!3d22.7196!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x3962fd24c9f2e5e5%3A0x5f5b6b6b6b6b6b6b!2sShri%20Vaishnav%20Institute%20of%20Management%20%26%20Science!5e0!3m2!1sen!2sin!4v1234567890"
        width="100%" height="200"
        style="border:0; border-radius:8px;"
        allowfullscreen="" loading="lazy">
        </iframe>
        """, unsafe_allow_html=True)

        st.markdown("""
        <a href="https://clickeffect.co.in/svim/" target="_blank"
        style="display:block; background:#1a237e; color:white;
        padding:10px; border-radius:8px; text-align:center;
        text-decoration:none; margin:5px 0;">
        🏛️ Take Virtual Tour of SVIMS
        </a>
        """, unsafe_allow_html=True)

        st.markdown("""
        <a href="https://maps.google.com/?q=Shri+Vaishnav+Institute+Management+Science+Indore"
        target="_blank"
        style="display:block; background:#0f6e56; color:white;
        padding:10px; border-radius:8px; text-align:center;
        text-decoration:none; margin:5px 0;">
        🗺️ Open in Google Maps
        </a>
        """, unsafe_allow_html=True)

    st.divider()

    if st.session_state.chat_history:
        chat_text = "\n\n".join([
            f"{'You' if m['role'] == 'user' else 'CampusBot'}: {m['content']}"
            for m in st.session_state.chat_history
        ])
        st.download_button(
            "💾 Save Chat",
            chat_text,
            "svims_chat.txt",
            use_container_width=True
        )

    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.chat_history = []
        st.rerun()

# =============================================
# MAIN CHAT AREA
# =============================================
st.markdown("# 🎓 SVIMS CampusBot")
st.markdown("*Shri Vaishnav Institute of Management & Science, Indore*")

if st.session_state.ready:
    st.success("🟢 CampusBot Active — Ask me anything!")
elif st.session_state.load_error:
    st.error("🔴 Bot failed to start. Check the error above.")
else:
    st.warning("⏳ Loading...")

st.divider()

if not st.session_state.chat_history:
    st.markdown("""
    <div class="bot-msg">
    👋 Hello! I am SVIMS CampusBot!<br><br>
    I can help you with:<br>
    📍 College location, virtual tour & maps<br>
    🎓 Courses & admission information<br>
    💼 Placement cell & career details<br>
    🎭 Clubs, activities & events<br>
    📚 Library, hostel & fees<br>
    👨‍🏫 Faculty & contact directory<br>
    📅 Academic calendar & events<br><br>
    Use the sidebar tabs for quick access!<br>
    Or type your question below! 👇
    </div>
    <div class="clearfix"></div>
    """, unsafe_allow_html=True)
else:
    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.markdown(f"""
            <div class="user-msg">{msg["content"]}</div>
            <div class="clearfix"></div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="bot-msg">{msg["content"]}</div>
            <div class="clearfix"></div>
            """, unsafe_allow_html=True)

st.divider()

# =============================================
# CHAT INPUT FORM
# =============================================
if st.session_state.ready:
    with st.form("chat_form", clear_on_submit=True):
        col1, col2 = st.columns([5, 1])
        with col1:
            user_input = st.text_input(
                "Ask a question...",
                placeholder="e.g. Who is the Director of SVIMS?",
                label_visibility="collapsed",
                max_chars=500
            )
        with col2:
            send = st.form_submit_button("Send 📤", type="primary")

    if send:
        if not user_input.strip():
            st.warning("⚠️ Please type a question!")
        elif len(user_input.strip()) < 3:
            st.warning("⚠️ Question too short!")
        else:
            st.session_state.chat_history.append({
                "role": "user", "content": user_input
            })
            with st.spinner("🤔 Finding answer..."):
                try:
                    answer = get_answer(st.session_state.chain, user_input)
                    if not answer or len(answer) < 5:
                        answer = "I don't have that information. Please contact svimi@svimi.org or call 0731-2789925"
                except Exception as e:
                    print(f"Chat error: {e}")
                    answer = "Something went wrong. Please try again or contact svimi@svimi.org"
            st.session_state.chat_history.append({
                "role": "bot", "content": answer
            })
            st.rerun()
else:
    if not st.session_state.load_error:
        st.info("⏳ CampusBot is loading...")

# =============================================
# FOOTER
# =============================================
st.divider()
st.markdown("""
<div style='text-align:center; color:gray; font-size:12px'>
🎓 SVIMS CampusBot | AI-Powered Campus Assistant<br>
Python + LangChain + FAISS + Streamlit + Groq AI |
<a href="https://www.svimi.org">www.svimi.org</a>
</div>
""", unsafe_allow_html=True)