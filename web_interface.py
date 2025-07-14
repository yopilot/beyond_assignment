"""Flask web interface for Reddit Persona Generator."""

import logging
import queue
import os
import json
import torch
from threading import Thread
from flask import Flask, render_template, request, jsonify, send_file
from reddit_persona_generator import RedditPersonaGenerator, current_status, generation_lock

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Global variables for progress tracking
progress_queue = queue.Queue()

# Initialize Flask app with proper static folder configuration
app = Flask(__name__, 
            static_folder='static',
            static_url_path='/static')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    """API endpoint to start persona generation."""
    global current_status, generation_lock
    
    try:
        data = request.json
        username = data.get('username', '').strip()
        
        if not username:
            return jsonify({'error': 'Username is required'}), 400
        
        # Check if generation is already running
        # Handle race conditions and stale locks by checking the actual status
        if generation_lock:
            # If marked as completed but lock wasn't cleared, force clear it
            if current_status.get("completed", False) or current_status.get("stage") == "error" or current_status.get("stage") == "completed":
                logging.warning(f"Stale generation lock detected. Status: {current_status.get('stage')}, Completed: {current_status.get('completed')}. Forcing reset.")
                generation_lock = False
                # Also reset the status to idle
                current_status.update({
                    "stage": "idle", 
                    "progress": 0, 
                    "message": "Ready (stale lock cleared)", 
                    "error": None, 
                    "completed": False
                })
            else:
                # Log the current status for debugging
                logging.info(f"Generation blocked - Lock: {generation_lock}, Status: {current_status}")
                # Only block if there's an active generation
                return jsonify({'error': 'Generation already in progress. Please wait for it to complete or refresh the page.'}), 409
        
        # Reset status for new generation using the global variable
        current_status.update({
            "stage": "starting", 
            "progress": 0, 
            "message": "Initializing...", 
            "error": None, 
            "completed": False
        })
        
        def run_generation():
            global generation_lock, current_status
            generator = None
            try:
                # Set generation lock to prevent multiple simultaneous generations
                generation_lock = True

                # Create fresh generator instance with proper progress callback
                def web_progress_callback(stage, progress, message):
                    """Progress callback that updates the global current_status"""
                    global current_status
                    current_status.update({
                        "stage": stage,
                        "progress": progress,
                        "message": message,
                        "completed": stage == "completed",
                        "error": None if stage != "error" else current_status.get("error")
                    })
                    logging.info(f"Progress update: {stage} {progress}% - {message}")

                generator = RedditPersonaGenerator()
                # Override the generator's progress callback to use our web callback
                generator.update_progress = web_progress_callback
                # Also update the component callbacks to ensure they use the web callback
                generator.scraper.progress_callback = web_progress_callback
                generator.persona_generator.progress_callback = web_progress_callback
                generator.file_manager.progress_callback = web_progress_callback

                # Generate persona (generator will handle all progress updates)
                output_file = generator.generate_full_persona(username)

                # Log the original output file path
                logging.info(f"Generation completed successfully: {output_file}")
                
                # Extract just the filename from the full path
                if '/' in output_file:
                    output_filename = output_file.split('/')[-1]
                elif '\\' in output_file:
                    output_filename = output_file.split('\\')[-1]
                else:
                    output_filename = output_file
                
                # Update current_status to ensure web interface has access to output_file
                current_status.update({
                    "stage": "completed",
                    "progress": 100,
                    "message": "Persona generation completed successfully!",
                    "completed": True,
                    "output_file": output_filename,
                    "error": None
                })
                
            except Exception as e:
                current_status.update({
                    "error": str(e),
                    "stage": "error",
                    "progress": 0,
                    "message": f"Error: {str(e)}",
                    "completed": False
                })
                logging.error(f"Generation failed: {e}")
            finally:
                # CRITICAL: Always clear the generation lock
                generation_lock = False

                # Clean up resources
                if generator and hasattr(generator, 'model_manager') and generator.model_manager:
                    try:
                        # Clear GPU cache if using CUDA
                        if torch.cuda.is_available():
                            torch.cuda.empty_cache()
                    except Exception as cleanup_error:
                        logging.warning(f"Cleanup warning: {cleanup_error}")
        
        thread = Thread(target=run_generation)
        thread.daemon = True
        thread.start()
        
        return jsonify({'status': 'started', 'message': f'Started generating persona for {username}'})
        
    except Exception as e:
        current_status = {"stage": "error", "progress": 0, "message": f"Failed to start: {str(e)}", "error": str(e), "completed": False}
        return jsonify({'error': str(e)}), 500

@app.route('/progress')
def get_progress():
    """API endpoint to get current progress."""
    global current_status
    try:
        return jsonify(current_status)
    except Exception as e:
        logging.error(f"Error in progress endpoint: {e}")
        # Return a fallback status in case of error
        return jsonify({
            "stage": "unknown", 
            "progress": 0, 
            "message": f"Error checking progress: {str(e)}", 
            "error": str(e), 
            "completed": False
        })

@app.route('/api/status')
def get_status():
    """API endpoint to get current status (same as progress but with lock info)."""
    global current_status, generation_lock
    try:
        status_with_lock = current_status.copy()
        status_with_lock['lock'] = generation_lock
        return jsonify(status_with_lock)
    except Exception as e:
        logging.error(f"Error in status endpoint: {e}")
        # Return a fallback status in case of error
        return jsonify({
            "stage": "unknown", 
            "progress": 0, 
            "message": f"Error checking status: {str(e)}", 
            "error": str(e), 
            "completed": False,
            "lock": generation_lock
        })

@app.route('/reset', methods=['POST'])
def reset_generation():
    """API endpoint to reset generation state."""
    global current_status, generation_lock
    try:
        # Log before reset
        logging.info(f"Resetting generation state. Previous state: Lock={generation_lock}, Status={current_status.get('stage')}")
        
        # Force reset the generation state
        current_status = {
            "stage": "idle", 
            "progress": 0, 
            "message": "Ready (manually reset)", 
            "error": None, 
            "completed": False, 
            "generation_id": None
        }
        
        # Force clear the lock
        generation_lock = False
        
        # Clear GPU cache if available
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            
        logging.info("Generation state successfully reset")
        return jsonify({'status': 'reset', 'message': 'Generation state has been reset'})
    except Exception as e:
        logging.error(f"Error during reset: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/download/<filename>')
def download_file(filename):
    """Download generated persona file."""
    try:
        # Remove 'output/' prefix if it exists in the filename
        clean_filename = filename.replace('output/', '').replace('output\\', '')
        
        # Use absolute path to output directory
        output_dir = os.path.abspath('output')
        filepath = os.path.join(output_dir, clean_filename)
        
        logging.info(f"Attempting to send file: {filepath}")
        
        if not os.path.exists(filepath):
            logging.error(f"File not found: {filepath}")
            return jsonify({'error': f'File not found: {filepath}'}), 404
            
        return send_file(filepath, as_attachment=True)
    except Exception as e:
        logging.error(f"Download error: {e}, filename: {filename}")
        return jsonify({'error': str(e)}), 404
        
@app.route('/persona_content/<filename>')
def get_persona_content(filename):
    """API endpoint to get the content of generated persona."""
    try:
        # Remove 'output/' prefix if it exists in the filename
        clean_filename = filename.replace('output/', '').replace('output\\', '')
        
        # Use absolute path to output directory
        output_dir = os.path.abspath('output')
        filepath = os.path.join(output_dir, clean_filename)
        
        logging.info(f"Reading persona content from: {filepath}")
        
        if not os.path.exists(filepath):
            logging.error(f"File not found: {filepath}")
            return jsonify({'error': f'File not found: {filepath}'}), 404
            
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        return jsonify({'content': content})
    except Exception as e:
        logging.error(f"Persona content error: {e}, filename: {filename}")
        return jsonify({'error': str(e)}), 404

@app.route('/sentiment_data/<filename>')
def get_sentiment_data(filename):
    """API endpoint to get the sentiment data JSON."""
    try:
        # Remove 'output/' prefix if it exists in the filename
        clean_filename = filename.replace('output/', '').replace('output\\', '')
        
        # Handle both persona and data filenames
        if '_persona_' in clean_filename:
            # Replace _persona_ with _data_ and change extension to .json
            data_filename = clean_filename.replace('_persona_', '_data_').replace('.txt', '.json')
        else:
            data_filename = clean_filename
            
        # Use absolute path to output directory
        output_dir = os.path.abspath('output')
        filepath = os.path.join(output_dir, data_filename)
        
        logging.info(f"Reading sentiment data from: {filepath}")
        
        # Check if file exists
        if not os.path.exists(filepath):
            logging.error(f"Sentiment data file not found: {filepath}")
            return jsonify({'error': f'File not found: {filepath}'}), 404
            
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        logging.info(f"Sentiment data keys: {list(data.keys())}")
            
        if 'sentiment_data' in data:
            logging.info(f"Sentiment data found in {filepath}")
            return jsonify({'sentiment_data': data['sentiment_data']})
        else:
            logging.warning(f"No sentiment_data found in {filepath}")
            return jsonify({'error': 'No sentiment data found in file', 'available_keys': list(data.keys())}), 404
    except Exception as e:
        logging.error(f"Sentiment data error: {e}, filename: {filename}")
        return jsonify({'error': str(e)}), 404

@app.route('/test')
def test_sentiment():
    """Test page for sentiment visualization."""
    return send_file('test_sentiment.html')


# New API endpoint for robust status/lock checking
@app.route('/api/status')
def api_status():
    """API endpoint to get both the lock and current status for frontend polling."""
    global current_status, generation_lock
    try:
        return jsonify({
            "lock": generation_lock,
            "stage": current_status.get("stage", "unknown"),
            "completed": current_status.get("completed", False),
            "has_error": current_status.get("error") is not None,
            "error": current_status.get("error"),
            "message": current_status.get("message"),
            "progress": current_status.get("progress", 0),
            "output_file": current_status.get("output_file"),
        })
    except Exception as e:
        logging.error(f"Error in api_status endpoint: {e}")
        return jsonify({"error": str(e)}), 500

def start_web_interface(host='127.0.0.1', port=5000, debug=True):
    """Start the web interface."""
    app.run(host=host, port=port, debug=debug)

if __name__ == '__main__':
    start_web_interface()
