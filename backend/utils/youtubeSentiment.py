import os
import time
import logging
from pathlib import Path
import json
from datetime import datetime
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from youtube_transcript_api import YouTubeTranscriptApi
from .ai_service import AIService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class YouTubeSentimentAnalyzer:
    def __init__(self):
        """Initialize the YouTube Sentiment Analyzer."""
        # Get API keys
        self.youtube_api_key = os.getenv('YOUTUBE_API_KEY')
        gemini_api_key = os.getenv('GEMINI_API_KEY')
        
        # Validate API keys
        if not self.youtube_api_key:
            raise ValueError("YouTube API key is required. Set YOUTUBE_API_KEY environment variable.")
        
        # Set channel ID
        self.channel_id = os.getenv('YOUTUBE_CHANNEL_ID') or 'UCjYKsjt-7EDU78KEcVbhYnQ'
        
        # Initialize YouTube API client
        self.youtube = build('youtube', 'v3', developerKey=self.youtube_api_key)
        
        # Initialize AI service
        self.ai_service = AIService(gemini_api_key)
        
        # Create results directory if it doesn't exist (anchored to backend/, not CWD)
        self.results_dir = Path(__file__).resolve().parent.parent / 'results'
        self.results_dir.mkdir(exist_ok=True)
    
    def get_latest_livestream_video(self, max_results=20, index=0):
        """Retrieve a completed livestream video by index (0=latest, 1=second latest, etc.)."""
        try:
            # Get uploads playlist ID
            request = self.youtube.channels().list(part='contentDetails', id=self.channel_id)
            response = request.execute()
            
            if not response.get('items'):
                logger.error(f"No channel found with ID: {self.channel_id}")
                return None
            
            uploads_playlist_id = response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
            
            # Get latest videos
            request = self.youtube.playlistItems().list(
                part='snippet', 
                playlistId=uploads_playlist_id, 
                maxResults=max_results
            )
            response = request.execute()
            
            if not response.get('items'):
                logger.info("No videos found in the channel.")
                return None
                
            video_ids = [item['snippet']['resourceId']['videoId'] for item in response['items']]
            
            # Check for completed livestreams
            request = self.youtube.videos().list(
                part='snippet,liveStreamingDetails', 
                id=','.join(video_ids)
            )
            response = request.execute()
            
            # Collect all completed livestreams
            completed_livestreams = []
            
            for item in response['items']:
                if ('liveStreamingDetails' in item and 
                    'actualEndTime' in item['liveStreamingDetails']):
                    video_title = item['snippet']['title']
                    video_id = item['id']
                    published_at = item['snippet']['publishedAt']
                    
                    completed_livestreams.append({
                        'id': video_id,
                        'title': video_title,
                        'published_at': published_at
                    })
            
            if not completed_livestreams:
                logger.info("No completed livestreams found in recent videos.")
                return None
                
            # Sort by publication date (newest first)
            completed_livestreams.sort(key=lambda x: x['published_at'], reverse=True)
            
            # Get the requested index (0 = latest, 1 = second latest, etc.)
            if index < len(completed_livestreams):
                selected_stream = completed_livestreams[index]
                logger.info(f"Selected livestream {index+1}: {selected_stream['title']} (ID: {selected_stream['id']})")
                return selected_stream
            else:
                logger.info(f"Requested livestream index {index} not available. Only found {len(completed_livestreams)} livestreams.")
                return None
                
        except HttpError as e:
            logger.error(f"Error fetching videos: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return None

    def get_transcript(self, video_id):
        """Get the English transcript of the video using youtube-transcript-api."""
        try:
            ytt_api = YouTubeTranscriptApi()
            fetched_transcript = ytt_api.fetch(video_id)

            transcript_list = ytt_api.list(video_id)
            print(f"Transcript list: {transcript_list}")
            
            if not fetched_transcript or len(fetched_transcript) == 0:
                logger.info(f"No transcript found for video ID: {video_id}")
                return None
                
            # Join all text snippets into a single string
            transcript_text = ' '.join([snippet.text for snippet in fetched_transcript])

            return transcript_text
            
        except Exception as e:
            logger.error(f"Error fetching transcript: {e}")
            return None

    def analyze_transcript(self, transcript, video_info):
        """Analyze transcript using AI service."""
        if len(transcript) > 15000:  # If transcript is very long
            logger.info("Transcript is long, splitting into chunks for analysis")
            
            # Define the prompt template for chunks
            chunk_prompt_template = """Analyze this portion of a stock trader's livestream transcript and provide:

1. Overall market conditions mentioned.
2. Specific stocks discussed, with analysis/opinions.
3. Overall sentiment (positive, negative, neutral).
4. Trade recommendations (stock, action: buy/sell, details).

This is chunk {chunk_num} of {total_chunks} from the transcript.

Transcript portion:

{content}"""
            
            # Get insights from each chunk
            insights = self.ai_service.analyze_large_content(
                prompt_template=chunk_prompt_template,
                text=transcript,
                max_chunk_size=10000
            )
            
            # Define summary prompt template
            summary_prompt_template = """Combine and summarize these analysis segments from different parts of a stock trader's livestream:

{insights}

Provide a final consolidated report with:
1. Overall market conditions mentioned.
2. Specific stocks discussed, with analysis/opinions.
3. Overall sentiment (positive, negative, neutral).
4. Trade recommendations (stock, action: buy/sell, details).
"""
            
            # Get final summary
            return self.ai_service.summarize_insights(
                summary_prompt_template=summary_prompt_template,
                insights=insights
            )
        
        else:
            # For shorter transcripts, analyze all at once
            prompt = """Analyze this stock trader's livestream transcript and provide:

1. Overall market conditions mentioned.
2. Specific stocks discussed, with analysis/opinions.
3. Overall sentiment (positive, negative, neutral).
4. Trade recommendations (stock, action: buy/sell, details).

Transcript:
"""
            return self.ai_service.analyze_content(prompt, transcript)

    def save_results(self, video_info, analysis, transcript=None):
        """Save analysis results to disk."""
        date_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        video_id = video_info['id']
        
        # Create video-specific directory
        video_dir = self.results_dir / f"{date_str}_{video_id}"
        video_dir.mkdir(exist_ok=True)
        
        # Save analysis
        with open(video_dir / 'analysis.txt', 'w', encoding='utf-8') as f:
            f.write(analysis)
        
        # Save video metadata
        with open(video_dir / 'video_info.json', 'w', encoding='utf-8') as f:
            json.dump(video_info, f, indent=2)
        
        # Save transcript if available
        if transcript:
            with open(video_dir / 'transcript.txt', 'w', encoding='utf-8') as f:
                f.write(transcript)
                
        logger.info(f"Results saved to {video_dir}")
        return str(video_dir)

    def process_latest_livestream(self, start_index=0, max_attempts=5):
        """Main function to process livestream and generate insights.
        Will try multiple videos if transcripts are unavailable."""
        
        for attempt in range(max_attempts):
            current_index = start_index + attempt
            logger.info(f"Trying video at index {current_index}...")
            
            # Get livestream at current index
            video_info = self.get_latest_livestream_video(index=current_index)

            if not video_info:
                logger.warning(f"No completed livestream found at index {current_index}.")
                continue
            
            # Get transcript
            transcript = self.get_transcript(video_info['id'])
            if not transcript:
                logger.warning(f"No English transcript available for video at index {current_index}. Trying next video...")
                continue
            
            # If we got here, we have a transcript!
            logger.info(f"Found video with transcript at index {current_index}: {video_info['title']}")
            
            # Analyze transcript
            logger.info("Analyzing transcript with AI service...")
            analysis = self.analyze_transcript(transcript, video_info)
            if not analysis:
                logger.warning("Failed to analyze transcript. Trying next video...")
                continue
            
            # Save results
            results_path = self.save_results(video_info, analysis, transcript)
            
            logger.info("Analysis complete!")
            return {
                'video_info': video_info,
                'analysis': analysis,
                'results_path': results_path
            }
        
        # If we've tried the maximum number of videos and none worked
        logger.error(f"Failed to find a video with an available transcript after {max_attempts} attempts.")
        return None

def main():
    try:
        analyzer = YouTubeSentimentAnalyzer()
        results = analyzer.process_latest_livestream(start_index=0, max_attempts=5)
        
        if results:
            print("\n=============== ANALYSIS RESULTS ===============\n")
            print(results['analysis'])
            print(f"\nResults saved to: {results['results_path']}")
        else:
            print("Could not find any videos with available transcripts to analyze.")
        
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")

if __name__ == '__main__':
    main()