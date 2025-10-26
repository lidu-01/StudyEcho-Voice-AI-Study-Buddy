import streamlit as st
import speech_recognition as sr
sr.flac_converter = "/opt/homebrew/bin"
import google.generativeai as genai
import json
import datetime
import pyttsx3
import PyPDF2
import io

# set up
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure API key
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    st.error("Please set up your GEMINI_API_KEY in the .env file")
    st.stop()

genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-2.5-flash')

st.set_page_config(page_title="StudyEcho", page_icon="🤖", layout="wide")
# Persistent storage for streak data
@st.cache_data(ttl=None)
def get_persistent_data():
    return {
        "streak_count": 0,
        "last_streak_date": None,
        "history": [],
        "plan_complete": 0
    }

# Initialize or load persistent data
persistent_data = get_persistent_data()

# streak Init with persistence
if "streak_count" not in st.session_state:
    st.session_state.streak_count = persistent_data["streak_count"]
if "last_streak_date" not in st.session_state:
    st.session_state.last_streak_date = persistent_data["last_streak_date"]
if "history" not in st.session_state:
    st.session_state.history = persistent_data["history"]
if "plan_complete" not in st.session_state:
    st.session_state.plan_complete = persistent_data["plan_complete"]

# Update persistent storage when session state changes
def update_persistent_storage():
    persistent_data["streak_count"] = st.session_state.streak_count
    persistent_data["last_streak_date"] = st.session_state.last_streak_date
    persistent_data["history"] = st.session_state.history
    persistent_data["plan_complete"] = st.session_state.plan_complete
    get_persistent_data.clear()

def update_study_streak():
    """Update streak counter based on daily use."""
    today = datetime.date.today()
    last_date = st.session_state.last_streak_date

    if last_date is None:
        st.session_state.streak_count = 1
        st.session_state.last_streak_date = today
    elif last_date == today:
        return
    elif (today - last_date).days == 1:
        st.session_state.streak_count += 1
    else:
        st.session_state.streak_count = 1
    st.session_state.last_streak_date = today
    
    # Update persistent storage
    update_persistent_storage()

# CSS style 
# -------------------- CUSTOM AESTHETIC STYLE -------------------- 
st.markdown("""
<style>
/* 🌸 Background Gradient */
.stApp {
  background: linear-gradient(120deg, #f6d1f2 0%, #c2e9fb 50%, #d4fc79 100%);
  background-attachment: fixed;
  font-family: "Inter", sans-serif;
}

/* 🫧 Soft floating pattern overlay */
.stApp::before {
  content: "";
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-image: radial-gradient(rgba(255,255,255,0.25) 2px, transparent 2px);
  background-size: 50px 50px;
  z-index: 0;
  opacity: 0.6;
}

/* 💻 Glass effect cards */
div[data-testid="stVerticalBlock"] > div {
  background: rgba(255, 255, 255, 0.45);
  backdrop-filter: blur(10px);
  border-radius: 18px;
  padding: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.05);
}

/* Headings & text */
h1, h2, h3, h4 {
  color: #2e2e2e;
}
p, span, div {
  color: #333;
}

/* Your Input subheader styling */
[data-testid="stHeader"] {
  color: #000000 !important;
}
.element-container div[data-testid="stMarkdown"] p {
  color: #000000 !important;
  font-weight: 600 !important;
}

/* Buttons */
button[kind="primary"] {
  background: linear-gradient(90deg, #ff9a9e 0%, #fad0c4 100%);
  color: white;
  font-weight: 600;
  border: none;
}
button[kind="primary"]:hover {
  background: linear-gradient(90deg, #fcb69f 0%, #ffecd2 100%);
  transform: scale(1.02);
  transition: all 0.2s ease-in-out;
}
button {
  border-radius: 8px !important;
}

/* Dropdown/Selectbox Styling */
div[data-baseweb="select"] {
    background-color: rgba(255, 255, 255, 0.5) !important;
    border-radius: 8px !important;
}

div[data-baseweb="select"] > div {
    background-color: transparent !important;
    color: #2e2e2e !important;
}

/* Reset Streak Button */
.stButton button {
    background: linear-gradient(90deg, #ff9a9e 0%, #fad0c4 100%) !important;
    color: white !important;
    font-weight: 600 !important;
    padding: 0.5rem 1rem !important;
    border: none !important;
    transition: all 0.2s ease !important;
}

.stButton button:hover {
    transform: scale(1.02) !important;
    background: linear-gradient(90deg, #fcb69f 0%, #ffecd2 100%) !important;
}

/* Text Input & Text Area */
.stTextInput input, .stTextArea textarea {
    background-color: rgba(255, 255, 255, 0.5) !important;
    border-radius: 8px !important;
    color: #2e2e2e !important;
    border: 1px solid rgba(0,0,0,0.1) !important;
}

/* Select Text Color */
.stSelectbox label, .stSelectbox div[data-baseweb="select"] span {
    color: #2e2e2e !important;
}

/* Sidebar style */
section[data-testid="stSidebar"] {
  background: rgba(255, 255, 255, 0.75) !important;
  backdrop-filter: blur(8px);
}

/* Sidebar Headers and Text */
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3,
section[data-testid="stSidebar"] h4 {
  color: #2e2e2e !important;
  font-weight: 600 !important;
  margin-top: 1rem !important;
}

/* Sidebar Metrics and Labels */
section[data-testid="stSidebar"] .stMetric label,
section[data-testid="stSidebar"] .stMetric div[data-testid="stMetricValue"] {
  color: #2e2e2e !important;
  font-weight: 500 !important;
}

/* Sidebar Info Messages */
section[data-testid="stSidebar"] .stAlert {
  background-color: rgba(255, 255, 255, 0.5) !important;
  color: #2e2e2e !important;
  border-color: rgba(0, 0, 0, 0.1) !important;
}

/* Sidebar Buttons */
section[data-testid="stSidebar"] .stButton button {
  width: 100% !important;
  margin: 0.25rem 0 !important;
  background: linear-gradient(90deg, #ff9a9e 0%, #fad0c4 100%) !important;
  color: white !important;
  font-weight: 600 !important;
  border: none !important;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1) !important;
}

section[data-testid="stSidebar"] .stButton button:hover {
  transform: scale(1.02) !important;
  background: linear-gradient(90deg, #fcb69f 0%, #ffecd2 100%) !important;
}

/* Make sidebar elements more visible */
section[data-testid="stSidebar"] {
  z-index: 1;
  position: relative;
}

/* Remove dark edges */
header, footer {background: transparent !important;}

/* File Uploader Styling */
.stFileUploader {
    background-color: rgba(255, 255, 255, 0.5) !important;
    border-radius: 8px !important;
    padding: 1rem !important;
    margin-bottom: 1rem !important;
}

/* PDF Content Area */
.stExpander {
    background-color: rgba(255, 255, 255, 0.5) !important;
    border-radius: 8px !important;
    margin-bottom: 1rem !important;
}

.stExpander textarea {
    background-color: white !important;
    color: #2e2e2e !important;
    font-family: monospace !important;
}
</style>
""", unsafe_allow_html=True)
# Sider-bar 
with st.sidebar:
    st.header("⚡ Quick Setup")
    subject = st.selectbox("📚 Subject:", ["CS", "Bio", "Econ", "General"])
    learning_style = st.selectbox("🧠 Learning Style:", ["Visual", "Auditory", "Hands-On"])
    
    st.header("🔥 Study Streak")
    st.metric("Current Streak", f"{st.session_state.streak_count} day(s)")
    if st.button("🔄 Reset Streak"):
        st.session_state.streak_count = 0
        st.session_state.last_streak_date = None

    st.header("📈 Your Progress")
    if st.session_state.history:
       st.metric("Sessions Completed", len(st.session_state.history))
    if st.button("Clear History"):
            st.session_state.history = []
            st.rerun()
    else:
        st.info("First session? Let's build momentum 🎯")

# VOICE FUNCTIONS 
def transcribe_voice(timeout=7):
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        # Reduce noise and adjust for ambient sound
        st.info("🎤 Adjusting for background noise...")
        recognizer.adjust_for_ambient_noise(source, duration=1)
        
        # Set dynamic energy threshold
        recognizer.energy_threshold = 300
        recognizer.dynamic_energy_threshold = True
        
        st.info("🎤 Listening... speak now!")
        try:
            # Shorter phrase timeout for better responsiveness
            audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=5)
            st.info("🔄 Processing speech...")
            text = recognizer.recognize_google(audio)
            return text
        except sr.WaitTimeoutError:
            st.warning("⏳ No voice detected. Try again.")
        except sr.UnknownValueError:
            st.error("❌ Couldn't understand audio.")
        except sr.RequestError:
            st.error("⚠️ Speech service error.")
    return ""

def speak_text(text):
    engine = pyttsx3.init()
    engine.setProperty("rate", 170)
    engine.say(text)
    engine.runAndWait()

# PDF Processing Function
def process_pdf(pdf_file):
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        total_chars = 0
        char_limit = 2000
        
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            remaining_chars = max(0, char_limit - total_chars)
            text += page_text[:remaining_chars] + "\n"
            total_chars += len(page_text[:remaining_chars])
            
            if total_chars >= char_limit:
                text += "\n... (text truncated to prevent token overflow)"
                break
                
        return text
    except Exception as e:
        st.error(f"Error processing PDF: {str(e)}")
        return None

#  HEADER 
st.markdown('<h3 style="color: #000000; font-weight: 600;">📝 Your Input</h3>', unsafe_allow_html=True)

# File Upload Section
uploaded_file = st.file_uploader("📎 Upload PDF (optional)", type=['pdf'])
if uploaded_file is not None:
    with st.spinner("Processing PDF..."):
        pdf_text = process_pdf(uploaded_file)
        if pdf_text:
            st.success("PDF processed successfully!")
            with st.expander("📄 PDF Content"):
                st.text_area("PDF Content", pdf_text, height=200)
            # Add PDF text to query if user wants
            if st.checkbox("Include PDF content in your query"):
                if "query" not in st.session_state:
                    st.session_state.query = ""
                st.session_state.query = f"{st.session_state.query}\n\nPDF Content:\n{pdf_text[:1000]}..."

# Text Input Area
query = st.text_area(
    "Type or use your voice:",
    placeholder="e.g., 'CS61A recursion is hard — explain with examples.'",
    label_visibility="collapsed",
    value=st.session_state.get('query', '')
)

col1, col2 = st.columns([3, 1])
with col1:
    if st.button("🎙️ Push to Talk (7s)", use_container_width=True):
        transcript = transcribe_voice(5)
        if transcript:
            st.session_state.query = transcript
            st.success(f"📝 Transcribed: {transcript}")
            query = transcript
            st.rerun()  # Refresh to update the text area

#  ANALYZE & GENERATE 
if st.button("🚀 Analyze & Generate Plan", type="primary") and query.strip():
    with st.spinner("Analyzing your input and generating a plan..."):
        clean_query = query.strip()
        #  1) Analyze 
        analysis_prompt = f"""
        Analyze this study struggle: "{clean_query}".
        Output ONLY valid JSON: {{
            "topic": "specific subject",
            "sentiment": "stressed/confused/motivated",
            "key_needs": ["2-3 concrete actions"]
        }}
        """
        try:
            analysis_resp = model.generate_content(analysis_prompt)
            raw_analysis = analysis_resp.text.strip().strip('```json').strip('```')
            analysis = json.loads(raw_analysis)
        except Exception as e:
            st.sidebar.error(f"⚠️ Analysis failed: {e}. using fallback.")
            analysis = {
                "topic": subject,
                "sentiment": "stressed",
                "key_needs": ["Review basics", "Practice problem", "Short break"]
            }

        #  2) Generate Plan 
        gen_prompt = f"""
        You are a helpful tutor. Create a 1-week study plan for: "{clean_query}".
        Learning style: {learning_style}.
        Sentiment: {analysis.get('sentiment', 'stressed')}.
        Include daily goals, resources, motivation boost, and 3 quiz questions.
        """
        try:
            gen_resp = model.generate_content(gen_prompt)
            output = gen_resp.text.strip()
        except Exception as e:
            st.error(f"⚠️ Plan generation error: {e}")
            output = "# Fallback Plan\nDay 1: Basics + examples.\nQuiz: 1. Print('Hi')."

        # 3) Save to History 
        current_time = datetime.datetime.now().isoformat()
        st.session_state.history.append({
            "query": query,
            "plan": output,
            "analysis": analysis,
            "timestamp": current_time
        })
        # 4 update streak
        update_study_streak()
        if st.session_state.streak_count in [3, 5, 10, 20]: 
            st.balloons()
            st.toast(f"🎉 Milestone! {st.session_state.streak_count}-day streak! keep going!", icon="🔥")

        #  5) Display Plan 
        st.subheader("📜 Your Custom Plan")
        st.markdown(output)

        #  6) Auto Speak Summary 
        plan_summary = (output.split("\n\n")[0] + " ... " + output.split("\n\n")[-1])[:200]
        speak_text(plan_summary)

st.markdown('</div>', unsafe_allow_html=True)

#  FOOTER 
st.markdown("---")
st.caption("🚀 Built for Cal Hacks 12.0 | Gemini + Voice Powered ✨")
