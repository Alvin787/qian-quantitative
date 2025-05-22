import os
import logging
import google.generativeai as genai
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AIService:
    def __init__(self, api_key=None):
        """Initialize the AI service with API key."""
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        
        if not self.api_key:
            raise ValueError("Gemini API key is required. Set GEMINI_API_KEY environment variable.")
        
        # Configure Gemini API
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash-preview-04-17')
    
    def analyze_content(self, prompt, text):
        """Analyze content using the configured AI model."""
        full_prompt = f"{prompt}\n\n{text}"
        
        try:
            response = self.model.generate_content(full_prompt)
            return response.text
        except Exception as e:
            logger.error(f"Error during AI API call: {e}")
            return None
    
    def analyze_large_content(self, prompt_template, text, max_chunk_size=10000):
        """Analyze large content by splitting it into chunks."""
        # Split text into manageable chunks
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), max_chunk_size):
            chunk = ' '.join(words[i:i + max_chunk_size])
            chunks.append(chunk)
        
        all_insights = []
        
        for i, chunk in enumerate(chunks):
            logger.info(f"Analyzing chunk {i+1}/{len(chunks)}")
            
            chunk_prompt = prompt_template.format(
                chunk_num=i+1,
                total_chunks=len(chunks),
                content=chunk
            )
            
            try:
                response = self.model.generate_content(chunk_prompt)
                all_insights.append(response.text)
                time.sleep(1)  # Rate limiting protection
            except Exception as e:
                logger.error(f"Error during AI API call for chunk {i+1}: {e}")
        
        return all_insights
    
    def summarize_insights(self, summary_prompt_template, insights):
        """Combine and summarize insights from multiple analyses."""
        combined_insights = ' '.join(insights)
        summary_prompt = summary_prompt_template.format(insights=combined_insights)
        
        try:
            final_response = self.model.generate_content(summary_prompt)
            return final_response.text
        except Exception as e:
            logger.error(f"Error during final AI API call: {e}")
            return "\n".join(insights)