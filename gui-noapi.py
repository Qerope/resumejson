import gradio as gr
import json
import subprocess
import os
import logging
from cohere import ClientV2
from pyppeteer import launch
from playwright.async_api import async_playwright

# Initialize logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize Cohere API
cohere_api_key = "39TAyPgeBqHh9rFoQLDtZL26dluSbjIqBBtjHnEa"  # Replace with your actual API key securely in production
cohere_client = ClientV2(api_key=cohere_api_key)

chat_prompt = "\nTailor this CV to apply for the following job position outline. USE THE SAME EXACT JSON FORMAT AND TRY TO KEEP THE SIZE RELEATIVELY THE SAME. Change, and improve wherever needed based on the first reference point and job description. Do not add anything not referred before. Try to only keep the relevant. Make sure skills and everything matches with whatever the job description is demanding. You are only allowed to change/add/modify skills section. Other sections may only be modified using the reference (except in description which you may add relevant points to the job posting)\n"

# Async function to generate PDF
async def generate_pdf_with_chromium(resume_html, output_pdf_path):
    try:
        logging.info("Starting Playwright browser to generate PDF...")
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)  # Launch Chromium browser
            logging.info("Chromium browser launched successfully.")

            context = await browser.new_context()
            page = await context.new_page()  # Create a new page
            logging.info("New page created in Chromium browser.")

            logging.info("Setting HTML content to the page...")
            await page.set_content(resume_html)  # Set the HTML content

            logging.info(f"Generating PDF and saving to {output_pdf_path}...")
            await page.pdf(path=output_pdf_path, format="letter")  # Generate PDF
            logging.info(f"PDF generated successfully at {output_pdf_path}")

            await browser.close()  # Close browser
            logging.info("Chromium browser closed.")
    except Exception as e:
        logging.error(f"Error during PDF generation: {e}")
        raise

# Function to summarize the job description and extract keywords
def summarize_job(job_description):
    logging.info("Starting job description summarization...")
    
    responseFormat = {
        "type": "json_object", 
        "json_schema": {
            "type": "object", 
            "properties": {
                "company": { "type": "string" }, 
                "job_title": { "type": "string" }, 
                "job_requirements": { "type": "string" }, 
                "job_keywords": { "type": "string" }, 
                "job_shortname": { "type": "string" }
            }, 
            "required": ["company", "job_title", "job_requirements", "job_keywords", "job_shortname"]
        }
    }
    
    try:
        # Call Cohere API to summarize job description
        logging.debug("Calling Cohere API to summarize the job description...")
        response = cohere_client.chat(
            messages=[
                { "role": "system", "content": "Generate a JSON formatted {company: String, job_title: String, job_requirements: String, job_keywords: String, job_shortname: String} for the provided job description. job_shortname must only include lowercase letters and underscores maximum 3 parts. job_keywords must include everything. job_requirements must include recommended." }, 
                { "role": "user", "content": job_description }
            ],
            response_format=responseFormat,
            safety_mode="OFF",
            model="command-r-plus-08-2024"
        )
        
        logging.debug(f"Cohere API response: {response.message.content[0].text}")
        
        jobdet = json.loads(response.message.content[0].text)
        jobtitle = jobdet['job_title']
        requirements = jobdet['job_requirements']
        keywords = jobdet['job_keywords']
        shortname = f"resume_{jobdet['job_shortname']}"
        company = jobdet['company']

        logging.info(f"Summarized job data: {jobtitle}, {requirements}, {keywords}, {shortname}")
        
        return {"company": company, "title": jobtitle, "requirements": requirements, "keywords": keywords, "shortname": shortname}
    
    except Exception as e:
        logging.error(f"Error summarizing job description: {str(e)}")
        raise

# Function to generate a tailored resume
async def generate_resume(cv_data_raw, job_data):
    logging.info("Starting resume generation...")
    
    try:
        # Load the CV data (assuming it's a JSON file)
        logging.debug("Loading CV data from selected file...")
        tailored_resume = json.loads(cv_data_raw)
        
        os.makedirs("./output/data", exist_ok=True)
        os.makedirs("./output/html", exist_ok=True)

        output_json_path = f"./output/data/{job_data['shortname']}.json"
        logging.debug(f"Saving tailored resume to JSON file: {output_json_path}")
        
        with open(output_json_path, 'w') as f:
            json.dump(tailored_resume, f, indent=2)

        # Convert to HTML using jsonresume CLI
        output_html_path = f"./output/html/{job_data['shortname']}.html"
        logging.debug(f"Running jsonresume CLI to convert JSON to HTML: {output_html_path}")
        
        subprocess.run([
            "resume", "export", output_html_path,
            "--resume", output_json_path,
            "--theme", "stackoverflow-crewshin"
        ], check=True)

        logging.info(f"Resume generated successfully: {output_html_path}")

        os.makedirs("./output/pdf", exist_ok=True)
        output_pdf_path = f"/output/pdf/{job_data['shortname']}.pdf"
        
        # Generate the PDF asynchronously
        resume_html = await display_html(output_html_path)  # Read HTML content
        await generate_pdf_with_chromium(resume_html, output_pdf_path)  # Generate PDF
        
        logging.info(f"Resume PDF generated successfully at {output_pdf_path}")
        return resume_html, f'<a href="{output_pdf_path}" > {output_pdf_path} </a>'   # Return the path to the HTML resume

    except Exception as e:
        logging.error(f"Error generating resume: {str(e)}")
        raise

# Function to display HTML content
async def display_html(file_path):
    logging.info(f"Displaying HTML content from file: {file_path}")
    try:
        with open(file_path, 'r') as f:
            html_content = f.read()
        return html_content
    except Exception as e:
        logging.error(f"Error reading HTML file: {str(e)}")
        return f"Error reading HTML file: {str(e)}"

# Gradio interface
def main_interface():
    with gr.Blocks() as demo:
        # Get list of JSON files in the References folder
        json_files = [f for f in os.listdir("./references") if f.endswith(".json")]
        
        with gr.Row():
            with gr.Column():
                cv_file_dropdown = gr.Dropdown(label="Step 1: Select CV File", choices=json_files, type="value")
                job_description = gr.Textbox(label="Job Description", lines=10)
            with gr.Column():
                job_data_display = gr.JSON(label="Extracted Job Data")
                summarize_btn = gr.Button("Step 2: Summarize Job Description")
            with gr.Column():
                chat_prompt_output = gr.Textbox(label="Step 3: Chat Prompt", lines=10)
            
        with gr.Row():
            with gr.Column():
                gen_cv_data = gr.Textbox(label="Generated Resume JSON", lines=10)
                generate_resume_btn = gr.Button("Step 4: Generate Resume")
            with gr.Column():
                html_display_link = gr.HTML(label="Generated Resume")
                html_display = gr.HTML(label="Generated Resume")
        
        # Event handlers
        def on_summarize(cv_file_dropdown, job_desc):
            logging.info(f"Job description received for summarization: {job_desc[:20]}...")  # Log first 20 chars for brevity
            jd = summarize_job(job_desc)
            
            # Get the selected CV file from the dropdown
            selected_cv_file = cv_file_dropdown
            
            # Build the correct path to the selected CV file
            cv_file_path = os.path.join("./references", selected_cv_file)
            
            # Open and read the selected CV file
            with open(cv_file_path, 'r') as file:
                resume_content = file.read()
                
            # Return job description data and the combined content
            return jd, (resume_content + chat_prompt + json.dumps(jd))  # Combine job data and prompt


        async def on_generate_resume(selected_cv_file, job_data):
            logging.info(f"Generating resume with data from selected CV file: {selected_cv_file}")
            
            # Load the selected CV file from the References folder
            cv_file_path = os.path.join("./references", selected_cv_file)
            with open(cv_file_path, 'r') as file:
                resume_data = file.read()
                
            return await generate_resume(resume_data, job_data)

        summarize_btn.click(on_summarize, inputs=[cv_file_dropdown, job_description], outputs=[job_data_display, chat_prompt_output])
        generate_resume_btn.click(on_generate_resume, inputs=[cv_file_dropdown, job_data_display], outputs=[html_display, html_display_link])

    return demo

# Launch the app
if __name__ == "__main__":
    logging.info("Launching Gradio app...")
    main_interface().launch(server_name="0.0.0.0", server_port=7860)
