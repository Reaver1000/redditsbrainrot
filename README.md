# redditsbrainrot
scrape reddit posts and generate brainrot videos. with emphasis on NO docker, NO paid apis and NO complex or tricky module installs
The reddit scraper has weights to slowly tune the best x posts ( chosen by you in setup) 

I have made this extremely modular, I want each building block working before i wrap it up in a pretty package.  
TTS is currently set to Bark, but you can substitute whatever model you want, just modify the tts.py file to your liking. The Bark model has some issues with installation, but it is working without too many issues 

Installation

Run Requirments and that should be 90% of the required modules until i can be bothered to recheck with a clean install. 
you will need pytorch, so download from https://pytorch.org/get-started/locally/ and select your cuda
You will also need the video editor https://ffmpeg.org/download.html#build-windows
Run Setup and that should set up and prompt you for most of the info you need.
All the modules run independently but some require to be run in the correct order. 
After setup is run, downloader lets you download some youtube videos and removes the audio ( some suggested links already in ) 
BGMdownloader is a background music downloader ( be aware you need to credit the source, in your description, not personally used )  
Audiostripper strips the audio of any external files you want to bring in
BGvideotomp4 does what it says on the tin. mass converts all in backgroundvideos folder to .mp4 to standardise the input in a ffmpeg friendly format. Takes awhile but only needs to be run once

Running:
If you want to check the flow, run in this order
Scraper
TTS
Subtitles 
BGM ( if you want a backing music track )
Video

When you are happy with how it runs, pulling up Main automates the entire run. 




Still to do  
move the current local CSV online so automatic posting is possible ( n8n, make, postiz etc ) 
allow a choice of folders for the final video ( also online ) 


