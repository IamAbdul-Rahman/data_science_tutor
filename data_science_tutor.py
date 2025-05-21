import streamlit as st
import google.generativeai as genai
from datetime import datetime

class ConversationMemory:
    def __init__(self, max_history=20):
        """
        Maximum number of exchanges to keep in memory
        """
        self.max_history = max_history
    
    def add_exchange(self, user_message, assistant_response):
        """
        Add a new exchange to the conversation history
        """
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []
        
        # Add the new exchange
        st.session_state.chat_history.append({
            "user": user_message,
            "assistant": assistant_response
        })
        
        # Trim history
        if len(st.session_state.chat_history) > self.max_history:
            st.session_state.chat_history = st.session_state.chat_history[-self.max_history:]
    
    def get_conversation_history(self):
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []
        
        return st.session_state.chat_history
    
    def clear(self):
        st.session_state.chat_history = []
        
    def format_for_prompt(self):
        """
        Formatted conversation history
        """
        history = self.get_conversation_history()
        formatted_history = ""
        
        for exchange in history:
            formatted_history += f"Human: {exchange['user']}\n"
            formatted_history += f"AI Tutor: {exchange['assistant']}\n\n"
            
        return formatted_history

class DataScienceTutor:
    def __init__(self, api_key, memory=None):
        self.api_key = api_key
        self.memory = memory if memory else ConversationMemory()
        self.configure_genai()
        
    def configure_genai(self):
        genai.configure(api_key=self.api_key)
        
    def get_system_prompt(self):
        return """
        You are a helpful and knowledgeable Data Science Tutor. Your purpose is to assist users with their data science related questions and problems.

        Guidelines:
        1. Only answer questions related to data science, statistics, machine learning, data analysis, programming for data science (Python, R, SQL), data visualization, or related fields.
        2. If the user asks questions unrelated to data science, politely redirect them and mention that you're specifically designed to help with data science topics.
        3. Provide clear, concise, and educational answers that help the user understand concepts.
        4. When appropriate, include code examples to illustrate concepts or solutions.
        5. If a concept is complex, break it down into simpler components.
        6. Maintain the context of the conversation and refer back to previous questions when relevant.
        
        Current date: {date}
        """
    
    def generate_response(self, user_message):
        """
        Generate a response to the user's message
        """
        try:
            # Get conversation history
            conversation_history = self.memory.format_for_prompt()
            
            # Create the model
            model = genai.GenerativeModel(
                model_name="gemini-2.0-flash",
                generation_config={
                    "temperature": 0.2,
                    "top_p": 0.95,
                    "top_k": 64,
                    "max_output_tokens": 2048,
                }
            )
            
            # Create the prompt with system instructions and history
            current_date = datetime.now().strftime("%B %d, %Y")
            system_prompt = self.get_system_prompt().format(date=current_date)
            
            prompt = f"{system_prompt}\n\nPrevious conversation:\n{conversation_history}\nHuman: {user_message}\nAI Tutor:"
            
            # Generate the response
            response = model.generate_content(prompt)
            
            # Return the response text
            return response.text
            
        except Exception as e:
            return f"Error generating response: {str(e)}"


# Streamlit UI
def main():
    # page configuration
    st.set_page_config(
        page_title="Data Science AI Tutor",
        page_icon="📊",
        layout="wide"
    )
    
    # Initialize session state for messages display
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # API key 
    try:
        api_key = st.secrets["API_KEY"]
        has_api_key = True
    except (KeyError, FileNotFoundError):
        has_api_key = False
    

    if not has_api_key:
        with st.sidebar:
            st.warning("API key not found in secrets. Please enter your Google API Key.")
            api_key = st.text_input("Enter your Google API Key:", type="password")
            if not api_key:
                st.error("API Key is required to use this application")
                st.info("""
                To set up your API key in Streamlit secrets:
                
                1. Local development: Create a file `.streamlit/secrets.toml` with:
                   ```
                   GOOGLE_API_KEY = "your-api-key"
                   ```
                
                2. Streamlit Cloud: Add the GOOGLE_API_KEY to your app secrets
                   in the Streamlit Cloud dashboard.
                """)
                st.stop()
    
    # Initialize memory and tutor
    if 'memory' not in st.session_state:
        st.session_state.memory = ConversationMemory()
    
    if 'tutor' not in st.session_state or 'api_key' not in st.session_state or st.session_state.api_key != api_key:
        st.session_state.tutor = DataScienceTutor(api_key, st.session_state.memory)
        st.session_state.api_key = api_key
    
    # App interface
    st.title("📊 Data Science AI Tutor")
    st.markdown("""
    This AI tutor is designed to help you with data science concepts, programming, statistics, and more.
    Ask any data science related question to get started!
    """)
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Input field for user questions
    if user_query := st.chat_input("Ask a data science question..."):
        # Add user message to chat history for display
        st.session_state.messages.append({"role": "user", "content": user_query})
        with st.chat_message("user"):
            st.markdown(user_query)
        
        # Display assistant thinking indicator
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            message_placeholder.markdown("Thinking...")
            
            # Get response from tutor
            tutor = st.session_state.tutor
            response = tutor.generate_response(user_query)
            
            # Update the conversation memory
            st.session_state.memory.add_exchange(user_query, response)
            
            # response
            message_placeholder.markdown(response)
            
            # assistant response to messages for display
            st.session_state.messages.append({"role": "assistant", "content": response})
    
    # Add a sidebar with information
    with st.sidebar:
        st.header("About this Tutor")
        st.info("""
        Data Science AI Tutor is powered by Google's Gemini 1.5 Pro model and designed to help you learn data scienceconcepts and solve related problems.
        
        **Topics you can ask about:**
        - Machine Learning algorithms
        - Statistical methods
        - Python, R, SQL for data science
        - Data visualization techniques
        - Data cleaning and preprocessing
        - And more data science related topics!
        """)
        
        # Add a button to clear conversation
        if st.button("Clear Conversation"):
            st.session_state.messages = []
            st.session_state.memory.clear()
            st.rerun()

if __name__ == "__main__":
    main()
