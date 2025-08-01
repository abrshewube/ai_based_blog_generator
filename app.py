import os
import streamlit as st
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_google_genai import GoogleGenerativeAI
from utils.config import Config
from utils.seo_tools import FreeSEOTools as SEOTools
import pandas as pd
from datetime import datetime
import markdown

# Set up Streamlit app
st.set_page_config(
    page_title="AI Blog Writer with Free SEO Tools",
    page_icon="✍️",
    layout="wide"
)

# Initialize Gemini LLM - CORRECTED VERSION
llm = GoogleGenerativeAI(
    model="gemini-2.5-flash",  # Changed from "models/gemini-pro"
    google_api_key=Config.GOOGLE_API_KEY,
    temperature=0.7,
    max_output_tokens=2048
)

# Load templates
def load_template(template_name):
    with open(f"templates/{template_name}", "r") as f:
        return f.read()

blog_template = PromptTemplate.from_template(load_template("blog_template.txt"))
seo_template = PromptTemplate.from_template(load_template("seo_template.txt"))

# Initialize chains
blog_chain = LLMChain(llm=llm, prompt=blog_template, verbose=True)
seo_chain = LLMChain(llm=llm, prompt=seo_template, verbose=True)

# App functions
def generate_blog_post(topic, word_count, keywords, tone, audience, competitor_analysis):
    """Generate blog post using AI"""
    with st.spinner("Generating blog post..."):
        response = blog_chain.run({
            "topic": topic,
            "word_count": word_count,
            "keywords": keywords,
            "tone": tone,
            "audience": audience,
            "competitor_analysis": competitor_analysis
        })
    return response

def analyze_seo(text, keywords):
    """Analyze text for SEO optimization"""
    with st.spinner("Analyzing SEO..."):
        response = seo_chain.run({
            "text": text,
            "keywords": keywords
        })
    return response

def save_output(content, filename_prefix="blog"):
    """Save generated content to file"""
    os.makedirs("outputs", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"outputs/{filename_prefix}_{timestamp}.md"
    
    with open(filename, "w") as f:
        f.write(content)
    
    return filename

def display_competitor_analysis(search_query):
    """Display competitor analysis results"""
    with st.spinner(f"Analyzing top results for '{search_query}'..."):
        competitor_df = SEOTools.analyze_competitors(search_query)
        
    if not competitor_df.empty:
        st.subheader("Top Search Competitors Analysis")
        st.dataframe(competitor_df)
        
        # Extract common keywords from competitors
        all_text = " ".join(competitor_df['Title'].fillna('') + " " + competitor_df['H1'].fillna(''))
        common_keywords = SEOTools.extract_keywords(all_text)
        
        if common_keywords:
            st.write("**Common keywords in top results:**", ", ".join(common_keywords[:5]))
        
        return competitor_df.to_markdown()
    else:
        st.warning("No competitor data found. Please check your search query.")
        return ""

# Main app
def main():
    st.title("✍️ AI-Powered Blog/Article Writer with Free SEO Tools")
    st.write("Generate high-quality, SEO-optimized content using free tools")
    
    with st.sidebar:
        st.header("⚙️ Settings")
        word_count = st.slider("Word Count", 500, 3000, 1000, 100)
        tone = st.selectbox("Tone", ["Professional", "Casual", "Informative", "Persuasive", "Friendly"])
        audience = st.selectbox("Target Audience", ["General", "Business", "Technical", "Beginners", "Experts"])
        
        st.header("🔍 SEO Analysis")
        search_query = st.text_input("Search Query for Competitor Analysis", 
                                   help="What people would search to find this article")
        analyze_competitors = st.button("Analyze Top Competitors")
    
    # Main content area
    tab1, tab2 = st.tabs(["📝 Generate Blog Post", "📊 SEO Analysis"])
    
    with tab1:
        st.subheader("Create New Blog Post")
        topic = st.text_input("Blog Topic/Title", placeholder="Enter your blog topic or title here...")
        keywords_input = st.text_input("Target Keywords (comma separated)", 
                                     placeholder="seo, content marketing, ai writing",
                                     help="Main keywords you want to rank for")
        
        if st.button("✨ Generate Blog Post"):
            if not topic:
                st.error("Please enter a blog topic")
                return
            
            keywords = [k.strip() for k in keywords_input.split(",")] if keywords_input else []
            competitor_analysis = ""
            
            if search_query:
                competitor_analysis = display_competitor_analysis(search_query)
            
            # Generate the blog post
            blog_content = generate_blog_post(
                topic=topic,
                word_count=word_count,
                keywords=", ".join(keywords),
                tone=tone,
                audience=audience,
                competitor_analysis=competitor_analysis
            )
            
            st.subheader("📄 Generated Blog Post")
            st.markdown(blog_content)
            
            # Save output
            saved_file = save_output(blog_content)
            st.success(f"✅ Blog post saved to {saved_file}")
            
            # Show SEO analysis
            if keywords:
                with st.expander("🔎 SEO Recommendations"):
                    seo_recommendations = analyze_seo(blog_content, ", ".join(keywords))
                    st.markdown(seo_recommendations)
                    
                    # Readability analysis
                    readability = SEOTools.calculate_readability(blog_content)
                    st.subheader("📈Readability Metrics")
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Word Count", readability['word_count'])
                    col2.metric("Avg Sentence Length", readability['avg_sentence_length'])
                    col3.metric("Reading Level", readability['reading_level'])
                    
                    # Meta tags suggestion
                    st.subheader("🏷️ Suggested Meta Tags")
                    meta_tags = SEOTools.generate_meta_tags(
                        title=topic,
                        description=blog_content[:160],
                        keywords=keywords
                    )
                    st.code(meta_tags, language='html')
    
    with tab2:
        st.subheader("SEO Text Analysis")
        seo_text = st.text_area("Paste your text here for SEO analysis", 
                              height=300,
                              placeholder="Paste your article content here...")
        seo_keywords = st.text_input("Keywords for analysis (comma separated)",
                                   help="Optional: Add target keywords for more specific analysis")
        
        if st.button("🔍 Analyze Text"):
            if not seo_text:
                st.error("Please enter text to analyze")
                return
            
            keywords = [k.strip() for k in seo_keywords.split(",")] if seo_keywords else []
            extracted_keywords = SEOTools.extract_keywords(seo_text)
            
            st.write("**Extracted Keywords:**", ", ".join(extracted_keywords[:10]))
            
            # SEO recommendations
            seo_recommendations = analyze_seo(seo_text, ", ".join(keywords + extracted_keywords[:5]))
            st.markdown(seo_recommendations)
            
            # Readability analysis
            readability = SEOTools.calculate_readability(seo_text)
            st.subheader("📊 Readability Metrics")
            st.json(readability)
            
            # Suggested meta tags if title is provided
            if seo_text.count('\n') > 2:
                first_line = seo_text.split('\n')[0]
                if len(first_line) < 120:  # Likely a title
                    st.subheader("🏷️ Suggested Meta Tags")
                    meta_tags = SEOTools.generate_meta_tags(
                        title=first_line,
                        description=' '.join(seo_text.split()[:25]),
                        keywords=extracted_keywords[:5]
                    )
                    st.code(meta_tags, language='html')


if __name__ == "__main__":
    main()