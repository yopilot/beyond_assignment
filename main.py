"""Main entry point for Reddit Persona Generator."""

import argparse
import sys
import torch
from reddit_persona_generator import RedditPersonaGenerator
from web_interface import start_web_interface

def show_gpu_info():
    """Show GPU information."""
    print("=== GPU INFORMATION ===")
    print(f"PyTorch version: {torch.__version__}")
    print(f"CUDA available: {torch.cuda.is_available()}")
    
    if torch.cuda.is_available():
        print(f"CUDA version: {torch.version.cuda}")
        print(f"Number of GPUs: {torch.cuda.device_count()}")
        for i in range(torch.cuda.device_count()):
            gpu_name = torch.cuda.get_device_name(i)
            memory_total = torch.cuda.get_device_properties(i).total_memory / 1024**3
            print(f"GPU {i}: {gpu_name} ({memory_total:.1f}GB)")
    else:
        print("No GPU detected. To enable GPU acceleration:")
        print("1. Install NVIDIA GPU drivers")
        print("2. Run: python setup_gpu.py")

def main():
    """Main function for command line usage."""
    parser = argparse.ArgumentParser(description='Generate a Reddit user persona.')
    parser.add_argument('username', nargs='?', help='Reddit username to analyze')
    parser.add_argument('--web', action='store_true', help='Start web interface')
    parser.add_argument('--host', default='127.0.0.1', help='Host for web interface')
    parser.add_argument('--port', type=int, default=5000, help='Port for web interface')
    parser.add_argument('--gpu-info', action='store_true', help='Show GPU information and exit')
    
    args = parser.parse_args()
    
    if args.gpu_info:
        show_gpu_info()
        return
    
    if args.web:
        print(f"Starting web interface at http://{args.host}:{args.port}")
        
        # Show GPU status at startup
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            print(f"🚀 GPU acceleration enabled: {gpu_name}")
        else:
            print("💡 Using CPU (GPU acceleration not available)")
            print("   For faster performance, run: python setup_gpu.py")
        
        start_web_interface(host=args.host, port=args.port, debug=True)
    elif args.username:
        try:
            generator = RedditPersonaGenerator()
            output_file = generator.generate_full_persona(args.username)
            print(f"\nPersona generation complete! Output saved to: {output_file}")
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)
    else:
        print("Please provide a username or use --web to start the web interface")
        print("Usage: python main.py <username> or python main.py --web")
        print("       python main.py --gpu-info (to check GPU status)")
        print("       python setup_gpu.py (to configure GPU acceleration)")

if __name__ == "__main__":
    main()
