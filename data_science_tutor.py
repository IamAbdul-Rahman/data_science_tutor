import streamlit as st
import google.generativeai as genai
from datetime import datetime

class ConversationMemory:
    """
    Handles storing and retrieving conversation history
    """
    
    def __init__(self, max_history=20):
        """
        Initialize the conversation memory
        
        Args:
            max_history (int): Maximum number of exchanges to keep in memory
        """
        self.max_history = max_history
    
    def add_exchange(self, user_message, assistant_response):
        """
        Add a new exchange to the conversation history
        
        Args:
            user_message (str): The user's message
            assistant_response (str): The assistant's response
        """
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []
        
        # Add the new exchange
        st.session_state.chat_history.append({
            "user": user_message,
            "assistant": assistant_response
        })
        
        # Trim history if it exceeds max_history
        if len(st.session_state.chat_history) > self.max_history:
            st.session_state.chat_history = st.session_state.chat_history[-self.max_history:]
    
    def get_conversation_history(self):
        """
        Get the current conversation history
        
        Returns:
            list: List of conversation exchanges
        """
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []
        
        return st.session_state.chat_history
    
    def clear(self):
        """Clear the conversation history"""
        st.session_state.chat_history = []
        
    def format_for_prompt(self):
        """
        Format the conversation history for inclusion in a prompt
        
        Returns:
            str: Formatted conversation history
        """
        history = self.get_conversation_history()
        formatted_history = ""
        
        for exchange in history:
            formatted_history += f"Human: {exchange['user']}\n"
            formatted_history += f"AI Tutor: {exchange['assistant']}\n\n"
            
        return formatted_history

class DataScienceTutor:
    """
    Data Science Tutor powered by Gemini 1.5 Pro
    """
    
    def __init__(self, api_key, memory=None):
        """
        Initialize the tutor
        
        Args:
            api_key (str): Google API key
            memory (ConversationMemory, optional): Memory instance
        """
        self.api_key = api_key
        self.memory = memory if memory else ConversationMemory()
        self.configure_genai()
        
    def configure_genai(self):
        """Configure the Google Generative AI client"""
        genai.configure(api_key=self.api_key)
        
    def get_system_prompt(self):
        """
        Get the system prompt for the tutor
        
        Returns:
            str: System prompt
        """
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
        
        Args:
            user_message (str): User's message
            
        Returns:
            str: Assistant's response
        """
        try:
            # Get conversation history
            conversation_history = self.memory.format_for_prompt()
            
            # Create the model
            model = genai.GenerativeModel(
                model_name="gemini-1.5-pro",
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


# Streamlit UI Implementation
def main():
    # Set page configuration
    st.set_page_config(
        page_title="Data Science AI Tutor",
        page_icon="📊",
        layout="wide"
    )
    
    # Initialize session state for messages display
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Check for API key
    if 'GOOGLE_API_KEY' not in st.session_state:
        with st.sidebar:
            api_key = st.text_input("Enter your Google API Key:", type="password")
            if api_key:
                st.session_state['GOOGLE_API_KEY'] = api_key
                st.success("API Key saved successfully!")
                # Initialize memory and tutor
                if 'memory' not in st.session_state:
                    st.session_state.memory = ConversationMemory()
                if 'tutor' not in st.session_state:
                    st.session_state.tutor = DataScienceTutor(api_key, st.session_state.memory)
            else:
                st.warning("Please enter your Google API Key to use the application")
                st.stop()
    
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
            
            # Display the response
            message_placeholder.markdown(response)
            
            # Add assistant response to messages for display
            st.session_state.messages.append({"role": "assistant", "content": response})
    
    # Add a sidebar with information
    with st.sidebar:
        st.header("About this Tutor")
        st.info("""
        This Data Science Tutor uses Gemini 1.5 Pro to answer your data science questions.
        
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
