# Workshopper v0.1.3n
*Workshopper is a simple little script written in Python for livery and mission makers to find and save their Steam Workshop statistics without having to painstakingly go through every single item themselves.*
- Workshopper requires an internet connection and the full ID or CustomLink of a Steam account in order to locate files
- Workshopper will automatically go through all workshop files on all user pages that are related to Nuclear Option (version v0.X.Xn), and automatically identify which ones to add
- Workshopper will automatically save the name, type, views, subscribers, favorites, awards, comments, changes, file size, upload date, latest update date, and description of every item
- Workshopper will prompt the user to export collected data as an Excel file, viewable via Microsoft Excel or Google Spreadsheets
- Workshopper primarily utilizes BeautifulSoup4, a web scraper library
- Workshopper cannot access any information that is not already public on steamcommunity.com. Private/unlisted items, along with item ratings, are not shown
Changelog:
- Fixed issues with file overlapping
- Added automatic airframe detection for livery files
- Added error correction for common issues relating to text characters in files
- Separated scraping algorithm from UI and console to improve performance
- Added multithreading support, up to 4 items processing at the same time (depending on calculated system performance)
Known issues:
- Doesn't work with anything other than Windows
- Save dialog won't open again if accidentally closed
- Won't overwrite preexisting files
