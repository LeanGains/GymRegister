# GymRegister Setup Guide

## Prerequisites

1. **Python 3.8 or higher**
2. **OpenAI API Key** (for AI-powered weight identification)
3. **Webcam or smartphone camera** (for taking photos)

## Installation

### 1. Clone the Repository
```bash
git clone https://github.com/LeanGains/GymRegister.git
cd GymRegister
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. OpenAI API Setup

#### Option A: Using Streamlit Secrets (Recommended)
1. Get your OpenAI API key from [OpenAI Platform](https://platform.openai.com/api-keys)
2. Create the secrets directory:
   ```bash
   mkdir .streamlit
   ```
3. Copy the example secrets file:
   ```bash
   cp .streamlit/secrets.toml.example .streamlit/secrets.toml
   ```
4. Edit `.streamlit/secrets.toml` and replace `your-openai-api-key-here` with your actual API key

#### Option B: Using Environment Variables
```bash
export OPENAI_API_KEY="your-openai-api-key-here"
```

### 4. Run the Application
```bash
streamlit run app.py
```

## Features Overview

### 🤖 AI-Powered Weight Identification
- **Computer Vision**: Uses OpenAI's GPT-4 Vision to automatically identify weights from photos
- **Smart Detection**: Recognizes dumbbells, plates, kettlebells, and other gym equipment
- **Weight Reading**: Automatically reads weight values from equipment
- **Condition Assessment**: Evaluates equipment condition from images

### 🔍 Asset Tag Recognition (OCR)
- **Text Detection**: Uses EasyOCR to detect asset tags in images
- **Multiple Formats**: Supports various asset tag formats
- **High Accuracy**: Optimized for gym equipment tags

### 📱 Dual Input Methods
- **Camera Capture**: Take photos directly in the app
- **File Upload**: Upload existing images from your device

## Usage Workflow

### Quick Asset Registration
1. **Take a Photo**: Use your camera or upload an image of gym equipment
2. **AI Analysis**: Click "🤖 AI Weight Identification" to analyze the image
3. **Review Results**: The AI will identify equipment type, weight, and condition
4. **Quick Register**: Use the pre-filled form to register assets instantly
5. **Asset Tag**: Add your gym's asset tag for tracking

### Traditional OCR Scanning
1. **Capture Image**: Take a photo showing asset tags clearly
2. **OCR Detection**: Click "🔍 Detect Asset Tags (OCR)" to find tags
3. **Database Check**: System checks if assets are already registered
4. **Location Update**: Update asset locations during inventory checks

### Complete Analysis
- Use "🚀 Complete Analysis (OCR + AI)" for comprehensive scanning
- Gets both asset tags and equipment identification in one operation

## Best Practices

### Photography Tips
- **Good Lighting**: Ensure adequate lighting for clear images
- **Clear View**: Make sure equipment numbers/weights are visible
- **Stable Shot**: Hold camera steady to avoid blur
- **Close-up**: Get close enough to read weight markings clearly

### Gym Layout Optimization
- **Organized Racks**: Keep equipment in designated rack positions
- **Clear Labeling**: Ensure asset tags are visible and unobstructed
- **Zone Mapping**: Use consistent location naming (e.g., "Free Weight Area - Rack 3")

### Asset Tag Management
- **Consistent Format**: Use standardized asset tag formats
- **Durable Tags**: Use weather-resistant tags that won't fade
- **Strategic Placement**: Place tags where they're visible but won't interfere with use

## Troubleshooting

### OpenAI API Issues
- **API Key Error**: Verify your API key is correct and has sufficient credits
- **Rate Limits**: If you hit rate limits, wait a few minutes before retrying
- **Model Access**: Ensure you have access to GPT-4 Vision (may require paid plan)

### OCR Issues
- **Poor Recognition**: Try better lighting or clearer images
- **False Positives**: Adjust OCR confidence thresholds in code if needed
- **Missing Tags**: Ensure tags are clearly visible and not obscured

### Camera Issues
- **Permission Denied**: Allow camera access in your browser
- **Poor Quality**: Check camera settings and lighting
- **Upload Alternative**: Use file upload if camera isn't working

## Database Management

### Backup
The SQLite database (`gym_assets.db`) contains all your asset data. Regular backups are recommended:
```bash
cp gym_assets.db gym_assets_backup_$(date +%Y%m%d).db
```

### Export Data
Use the "📥 Download as CSV" feature in the "View All Assets" section to export your data.

## Security Considerations

- **API Key Protection**: Never commit your OpenAI API key to version control
- **Local Database**: The SQLite database is stored locally - consider encryption for sensitive data
- **Network Security**: Use HTTPS in production deployments

## Cost Considerations

### OpenAI API Costs
- GPT-4 Vision API charges per image analyzed
- Typical cost: $0.01-0.03 per image depending on resolution
- Monitor usage in your OpenAI dashboard
- Consider batch processing for large inventories

### Optimization Tips
- Use "AI Weight Identification" selectively for new/unknown equipment
- Use OCR for routine asset tag scanning (free)
- Combine both methods only when necessary

## Support

For issues or questions:
1. Check this setup guide
2. Review the main README.md
3. Check OpenAI API documentation
4. Create an issue in the GitHub repository

## Next Steps

After setup:
1. Register your existing equipment using the "Register New Asset" page
2. Create a systematic scanning routine for inventory checks
3. Train staff on the photography best practices
4. Set up regular backup procedures
5. Monitor API usage and costs