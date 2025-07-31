wget https://github.com/WeJZTeam/JZFileBrowser/archive/refs/heads/main.zip && \
unzip main.zip "JZFileBrowser-main/JZFileBrowser/*" -d temp_dir && \
mv temp_dir/JZFileBrowser-main/* . && \
rm -rf main.zip temp_dir JFileBrowser-main && \


wget https://raw.githubusercontent.com/WeJZTeam/JZFileBrowser/main/start.sh
chmod +x start.sh
