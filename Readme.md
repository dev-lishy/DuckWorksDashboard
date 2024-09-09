### Dashboard - GIF Logo followed by Messages
This Dashboard displays the Duck Works lab logo followed by messages (e.g. current value of gold assets and percent value increase). This dashboard works on the Adafruit 64x64 pixel matrix display with the MatrixPortal M4 uc. 

![](https://github.com/dev-lishy/DuckWorksDashboard/blob/main/duckWalk.gif)

### Convert black and white gif to colorized using Image Magick cmd line

https://imagemagick.org/Usage

```convert duckWalkLarge.gif -coalesce -resize 64x64\! -level 10%,90% -colorize 90,85,170 duckWalk.gif```

### Resources

Circuit Python Ref Material https://github.com/todbot/circuitpython-tricks

Memory management tips: https://learn.adafruit.com/Memory-saving-tips-for-CircuitPython
