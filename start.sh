pip install --upgrade pip
pip install flask werkzeug
# Run the application
echo -e "${GREEN}"
echo "Starting JZFileBrowser..."
echo -e "Access at: ${BLUE}http://localhost:5000${GREEN}"
echo "Press Ctrl+C to stop"
echo -e "${NC}"
python JZFileBrowser/main.py
