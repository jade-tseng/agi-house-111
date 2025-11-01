import streamlit as st
import os
from pymongo import MongoClient
from datetime import datetime
from openai import OpenAI

# Page configuration
st.set_page_config(
    page_title="Health Economics Research App",
    page_icon="🏥",
    layout="wide"
)

# Initialize MongoDB connection
@st.cache_resource
def init_mongo():
    mongo_uri = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")
    db_name = os.environ.get("MONGO_DB", "app_database")
    client = MongoClient(mongo_uri)
    return client[db_name]

# Initialize OpenAI client
@st.cache_resource
def init_openai():
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return None
    return OpenAI(api_key=api_key)

db = init_mongo()
openai_client = init_openai()

# System message for research queries
SYSTEM_MESSAGE = """
You are a professional researcher preparing a structured, data-driven report on behalf of a global health economics team. Your task is to analyze the health question the user poses.

Do:
- Focus on data-rich insights: include specific figures, trends, statistics, and measurable outcomes (e.g., reduction in hospitalization costs, market size, pricing trends, payer adoption).
- When appropriate, summarize data in a way that could be turned into charts or tables, and call this out in the response (e.g., "this would work well as a bar chart comparing per-patient costs across regions").
- Prioritize reliable, up-to-date sources: peer-reviewed research, health organizations (e.g., WHO, CDC), regulatory agencies, or pharmaceutical earnings reports.
- Include inline citations and return all source metadata.

Be analytical, avoid generalities, and ensure that each section supports data-backed reasoning that could inform healthcare policy or financial modeling.
"""

# App title and description
st.title("🏥 Health Economics Research App")
st.markdown("Research health economics topics and manage bills using AI-powered analysis")

# Sidebar
with st.sidebar:
    st.header("Navigation")
    page = st.radio("Select Page", ["Research Query", "Bills Manager", "Query History"])
    
    st.divider()
    st.subheader("Database Stats")
    
    # Show database statistics
    try:
        queries_count = db.queries.count_documents({})
        bills_count = db.bills.count_documents({})
        st.metric("Total Queries", queries_count)
        st.metric("Total Bills", bills_count)
    except Exception as e:
        st.error(f"Database connection error: {e}")

# Research Query Page
if page == "Research Query":
    st.header("💡 Research Query")
    
    if not openai_client:
        st.warning("⚠️ OpenAI API key not configured. Please set OPENAI_API_KEY environment variable.")
    else:
        user_query = st.text_area(
            "Enter your health economics research question:",
            placeholder="e.g., Research the economic impact of semaglutide on global healthcare systems.",
            height=100
        )
        
        col1, col2 = st.columns([1, 5])
        with col1:
            if st.button("🔍 Research", type="primary"):
                if user_query:
                    with st.spinner("Analyzing your query..."):
                        try:
                            response = openai_client.chat.completions.create(
                                model="gpt-4o",
                                messages=[
                                    {"role": "system", "content": SYSTEM_MESSAGE},
                                    {"role": "user", "content": user_query}
                                ]
                            )
                            
                            result = response.choices[0].message.content
                            
                            # Display result
                            st.subheader("Research Results")
                            st.markdown(result)
                            
                            # Save to MongoDB
                            query_doc = {
                                "query": user_query,
                                "result": result,
                                "timestamp": datetime.now(),
                                "model": "gpt-4o"
                            }
                            db.queries.insert_one(query_doc)
                            st.success("✅ Results saved to database")
                            
                        except Exception as e:
                            st.error(f"Error: {e}")
                else:
                    st.warning("Please enter a research question")

# Bills Manager Page
elif page == "Bills Manager":
    st.header("📄 Bills Manager")
    
    tab1, tab2 = st.tabs(["Upload Bill", "View Bills"])
    
    with tab1:
        st.subheader("Upload a new bill")
        
        uploaded_file = st.file_uploader("Choose a file", type=['pdf', 'png', 'jpg', 'jpeg', 'txt'])
        
        if uploaded_file is not None:
            col1, col2 = st.columns(2)
            with col1:
                st.write("**Filename:**", uploaded_file.name)
                st.write("**File size:**", f"{uploaded_file.size / 1024:.2f} KB")
            
            if st.button("💾 Submit Bill", type="primary"):
                try:
                    # Save bill metadata to MongoDB
                    bill_doc = {
                        "filename": uploaded_file.name,
                        "size": uploaded_file.size,
                        "status": "pending",
                        "uploaded_at": datetime.now()
                    }
                    result = db.bills.insert_one(bill_doc)
                    
                    st.success(f"✅ Bill submitted successfully! ID: {result.inserted_id}")
                except Exception as e:
                    st.error(f"Error submitting bill: {e}")
    
    with tab2:
        st.subheader("All Bills")
        
        try:
            bills = list(db.bills.find().sort("uploaded_at", -1))
            
            if bills:
                for bill in bills:
                    with st.expander(f"📄 {bill['filename']} - {bill['status']}"):
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.write("**ID:**", str(bill['_id']))
                        with col2:
                            st.write("**Status:**", bill['status'])
                        with col3:
                            st.write("**Uploaded:**", bill['uploaded_at'].strftime("%Y-%m-%d %H:%M"))
            else:
                st.info("No bills found. Upload your first bill!")
        except Exception as e:
            st.error(f"Error loading bills: {e}")

# Query History Page
elif page == "Query History":
    st.header("📊 Query History")
    
    try:
        queries = list(db.queries.find().sort("timestamp", -1).limit(10))
        
        if queries:
            for idx, query in enumerate(queries, 1):
                with st.expander(f"Query {idx}: {query['query'][:60]}..."):
                    st.write("**Full Query:**", query['query'])
                    st.write("**Timestamp:**", query['timestamp'].strftime("%Y-%m-%d %H:%M:%S"))
                    st.divider()
                    st.markdown("**Results:**")
                    st.markdown(query['result'])
        else:
            st.info("No queries found. Run your first research query!")
    except Exception as e:
        st.error(f"Error loading query history: {e}")

